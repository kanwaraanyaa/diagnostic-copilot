"""
RAG pipeline service — orchestrates retrieval, reranking, and LLM synthesis.
"""

from __future__ import annotations

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from typing import Any

from backend.schemas.patient import (
    Citation,
    DiagnosticReport,
    DifferentialCondition,
    PatientCase,
    UncertaintyLevel,
)
from backend.services.llm_service import BaseLLMProvider, get_llm_provider
from config import get_settings
from logger import get_logger
from patient.normalizer import patient_case_to_prompt
from rag.bm25 import BM25Index
from rag.citations import build_citations, format_citations_for_prompt
from rag.hybrid_search import hybrid_search
from rag.ingestion import ensure_indexes_loaded
from rag.reranker import rerank
from rag.vector_store import VectorStore

log = get_logger(__name__)


# ---- Query generation -------------------------------------------------------

def generate_search_queries(case: PatientCase) -> list[str]:
    """
    Generate targeted search queries from a patient case.
    Deterministic (no LLM needed) — extracts symptoms, labs, and history.
    """
    queries: list[str] = []

    # Primary symptom-based query
    if case.symptoms:
        queries.append(" ".join(case.symptoms))

    # Individual symptom queries for specificity
    for symptom in case.symptoms[:5]:
        queries.append(f"{symptom} clinical significance differential diagnosis")

    # Lab-based queries
    abnormal_labs = [lab for lab in case.labs if lab.is_abnormal]
    if abnormal_labs:
        lab_names = " ".join(l.name for l in abnormal_labs[:5])
        queries.append(f"abnormal {lab_names} clinical interpretation")

    # Combined query
    demo = ""
    if case.patient.age:
        demo = f"{case.patient.age} year old"
    if case.symptoms and demo:
        queries.append(f"{demo} presenting with {' '.join(case.symptoms[:3])}")

    # History-based
    if case.history:
        queries.append(f"medical history {' '.join(case.history[:3])} risk factors")

    # Clinical notes snippet
    if case.clinical_notes.strip():
        queries.append(case.clinical_notes.strip()[:200])

    # Deduplicate
    seen: set[str] = set()
    unique: list[str] = []
    for q in queries:
        q_lower = q.lower().strip()
        if q_lower not in seen and q_lower:
            seen.add(q_lower)
            unique.append(q)

    return unique[:8]  # Cap at 8 queries


# ---- Main RAG pipeline ------------------------------------------------------

SYSTEM_PROMPT = """You are a clinical decision-support research prototype.
You analyze patient information using ONLY the retrieved medical evidence provided.

CRITICAL RULES:
1. Only make claims supported by the provided evidence.
2. Cite evidence using the source IDs provided (e.g., [E1], [E2]).
3. If the evidence is insufficient, explicitly state: "Insufficient evidence in the retrieved sources."
4. NEVER fabricate citations or evidence.
5. NEVER provide definitive diagnoses — use language like "possible condition", "evidence suggests", "requires clinician verification".
6. NEVER prescribe medications or dosages.
7. NEVER make emergency decisions.
8. Distinguish between model findings and retrieved evidence.
9. Express uncertainty where appropriate.

You are a RESEARCH TOOL, not a replacement for medical professionals."""

ANALYSIS_PROMPT_TEMPLATE = """Analyze the following patient case using ONLY the retrieved evidence below.

--- PATIENT CASE ---
{patient_text}

--- RETRIEVED EVIDENCE ---
{evidence_text}

--- INSTRUCTIONS ---
Generate a clinical analysis in the following JSON format:
{{
    "patient_summary": "Brief summary of the patient presentation",
    "important_findings": ["finding 1", "finding 2"],
    "differential_considerations": [
        {{
            "condition": "Condition name",
            "supporting_evidence": ["Evidence supporting this condition, citing [E1] etc."],
            "contradicting_evidence": ["Evidence against, or empty list"],
            "uncertainty": "low|moderate|high",
            "source_ids": ["E1", "E2"]
        }}
    ],
    "suggested_questions": ["Clinical question to investigate further"],
    "missing_information": ["What additional information would help"]
}}

Remember:
- Cite evidence IDs for every claim.
- If evidence is insufficient, say so explicitly.
- Use "possible", "suggests", "may indicate" — never definitive language.
- Do NOT prescribe treatments.
"""


def run_rag_pipeline(
    case: PatientCase,
    vector_store: VectorStore | None = None,
    bm25_index: BM25Index | None = None,
    llm_provider: BaseLLMProvider | None = None,
) -> DiagnosticReport:
    """
    Full RAG pipeline:
    1. Generate queries from patient case.
    2. Hybrid retrieval (dense + sparse).
    3. Reranking.
    4. Build citations.
    5. LLM synthesis with evidence context.
    6. Parse and validate structured report.

    Returns a DiagnosticReport regardless of errors (errors are captured in the report).
    """
    log.info("rag_pipeline_start", case_id=case.case_id)
    errors: list[str] = []

    # Ensure indexes are loaded
    try:
        vs, bm = ensure_indexes_loaded(vector_store, bm25_index)
    except Exception as e:
        log.error("index_load_failed", error=str(e))
        return DiagnosticReport(
            case_id=case.case_id,
            patient_summary="Analysis could not be completed.",
            errors=[f"Failed to load knowledge base: {e}"],
        )

    # 1. Generate queries
    queries = generate_search_queries(case)
    log.info("queries_generated", count=len(queries))

    # 2. Retrieve evidence (merge results from all queries)
    all_results: dict[str, dict[str, Any]] = {}
    for query in queries:
        try:
            results = hybrid_search(query, vs, bm)
            for r in results:
                cid = r["chunk_id"]
                if cid not in all_results or r["score"] > all_results[cid]["score"]:
                    all_results[cid] = r
        except Exception as e:
            log.warning("retrieval_error", query=query[:80], error=str(e))
            errors.append(f"Retrieval error for query: {str(e)}")

    candidates = sorted(all_results.values(), key=lambda x: x["score"], reverse=True)
    log.info("retrieval_complete", unique_results=len(candidates))

    # 3. Rerank
    try:
        reranked = rerank(patient_case_to_prompt(case), candidates)
    except Exception as e:
        log.warning("reranking_failed", error=str(e))
        reranked = candidates[:get_settings().top_k_rerank]
        errors.append(f"Reranking failed, using raw results: {e}")

    # 4. Build citations
    citations = build_citations(reranked)

    # 5. LLM synthesis
    patient_text = patient_case_to_prompt(case)
    evidence_text = format_citations_for_prompt(citations)

    prompt = ANALYSIS_PROMPT_TEMPLATE.format(
        patient_text=patient_text,
        evidence_text=evidence_text,
    )

    try:
        llm = llm_provider or get_llm_provider()
        result_json = llm.generate_json(prompt, system_prompt=SYSTEM_PROMPT)
    except Exception as e:
        log.error("llm_generation_failed", error=str(e))
        return DiagnosticReport(
            case_id=case.case_id,
            patient_summary=f"Patient: {patient_text[:200]}",
            citations=citations,
            errors=[f"LLM generation failed: {e}"],
        )

    # 6. Parse structured output
    report = _parse_llm_report(case.case_id, result_json, citations, errors)
    log.info(
        "rag_pipeline_complete",
        case_id=case.case_id,
        conditions=len(report.differential_considerations),
        citations=len(report.citations),
        errors=len(report.errors),
    )
    return report


def _parse_llm_report(
    case_id: str,
    result: dict[str, Any],
    citations: list[Citation],
    errors: list[str],
) -> DiagnosticReport:
    """Parse LLM JSON output into a validated DiagnosticReport."""
    if result.get("parse_error"):
        errors.append("LLM output could not be parsed as JSON. Raw text is included.")
        return DiagnosticReport(
            case_id=case_id,
            patient_summary=result.get("raw_text", "Analysis failed.")[:500],
            citations=citations,
            errors=errors,
        )

    # Parse differential considerations
    differentials: list[DifferentialCondition] = []
    for d in result.get("differential_considerations", []):
        try:
            uncertainty_str = str(d.get("uncertainty", "unknown")).lower()
            try:
                uncertainty = UncertaintyLevel(uncertainty_str)
            except ValueError:
                uncertainty = UncertaintyLevel.UNKNOWN

            differentials.append(
                DifferentialCondition(
                    condition=str(d.get("condition", "Unknown condition")),
                    supporting_evidence=d.get("supporting_evidence", []),
                    contradicting_evidence=d.get("contradicting_evidence", []),
                    uncertainty=uncertainty,
                    source_ids=d.get("source_ids", []),
                )
            )
        except Exception as e:
            log.warning("differential_parse_error", error=str(e))

    return DiagnosticReport(
        case_id=case_id,
        patient_summary=str(result.get("patient_summary", "")),
        important_findings=result.get("important_findings", []),
        differential_considerations=differentials,
        suggested_questions=result.get("suggested_questions", []),
        citations=citations,
        errors=errors,
    )
