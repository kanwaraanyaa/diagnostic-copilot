"""
Agentic Query Planning and Multi-Hop Retrieval — Phase 3.
Decomposes complex clinical cases into sequential investigative hops:
1. Primary Symptom & Syndrome Exploration
2. Laboratory & Biomarker Stratification
3. Differential Exclusion & Complication Investigation
"""

from __future__ import annotations

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import Any, Optional
from pydantic import BaseModel, Field

from backend.schemas.patient import Citation
from config import get_settings
from logger import get_logger
from rag.bm25 import BM25Index
from rag.citations import build_citations
from rag.hybrid_search import hybrid_search
from rag.ingestion import ensure_indexes_loaded
from rag.reranker import rerank
from rag.vector_store import VectorStore

log = get_logger(__name__)


class QueryHop(BaseModel):
    """Represents a single step in a multi-hop retrieval plan."""
    hop_number: int
    focus_area: str  # e.g., "symptom_etiology", "biomarker_correlation", "differential_exclusion"
    query_text: str
    clinical_intent: str
    intermediate_insight: str = ""
    citations: list[Citation] = Field(default_factory=list)


class QueryPlanResult(BaseModel):
    """Result of an executed multi-hop query plan."""
    case_id: str = ""
    hops: list[QueryHop] = Field(default_factory=list)
    aggregated_citations: list[Citation] = Field(default_factory=list)
    query_synthesis: str = ""
    total_hops: int = 0


def generate_clinical_query_plan(patient_case: dict[str, Any], max_hops: int = 3) -> list[QueryHop]:
    """
    Formulates a structured 3-hop clinical query plan tailored to patient presentation.
    """
    symptoms = patient_case.get("symptoms", [])
    if isinstance(symptoms, str):
        symptoms = [s.strip() for s in symptoms.split(",") if s.strip()]

    history = patient_case.get("history", [])
    if isinstance(history, str):
        history = [h.strip() for h in history.split(",") if h.strip()]

    labs = patient_case.get("labs", [])
    abnormal_labs = []
    for l in labs:
        if isinstance(l, dict):
            name = l.get("name", "")
            val = l.get("value", "")
            unit = l.get("unit", "")
            is_ab = l.get("is_abnormal", False)
            if is_ab:
                abnormal_labs.append(f"{name} {val} {unit}".strip())

    hops: list[QueryHop] = []

    # Hop 1: Symptom & Syndrome Presentation
    symptom_terms = " ".join(symptoms[:4]) if symptoms else "clinical presentation"
    hop1_query = f"{symptom_terms} diagnosis clinical guidelines etiology"
    hops.append(
        QueryHop(
            hop_number=1,
            focus_area="symptom_etiology",
            query_text=hop1_query.strip(),
            clinical_intent="Investigate primary diagnostic criteria and etiology matching presenting symptoms.",
        )
    )

    # Hop 2: Biomarker / Laboratory Correlation
    if abnormal_labs:
        lab_terms = " ".join(abnormal_labs[:3])
        hop2_query = f"{lab_terms} clinical significance differential diagnosis laboratory reference"
    else:
        hop2_query = f"{symptom_terms} laboratory evaluation diagnostic workup biomarkers"

    hops.append(
        QueryHop(
            hop_number=2,
            focus_area="biomarker_correlation",
            query_text=hop2_query.strip(),
            clinical_intent="Assess diagnostic significance of laboratory markers and inflammatory trends.",
        )
    )

    if max_hops >= 3:
        # Hop 3: Differential Exclusion & Complications
        comorbidities = " ".join(history[:2]) if history else ""
        hop3_query = f"{symptom_terms} {comorbidities} differential exclusion complications red flags risk stratification"
        hops.append(
            QueryHop(
                hop_number=3,
                focus_area="differential_exclusion",
                query_text=hop3_query.strip(),
                clinical_intent="Identify critical rule-out conditions, contraindications, and complication thresholds.",
            )
        )

    return hops[:max_hops]


def execute_multi_hop_retrieval(
    patient_case: dict[str, Any],
    max_hops: int = 3,
    vs: Optional[VectorStore] = None,
    bm: Optional[BM25Index] = None,
) -> QueryPlanResult:
    """
    Executes iterative multi-hop retrieval across the knowledge base.
    At each hop, retrieves evidence, generates intermediate insights,
    and aggregates deduplicated citations tagged with provenance.
    """
    if vs is None or bm is None:
        vs, bm = ensure_indexes_loaded()

    settings = get_settings()
    hops = generate_clinical_query_plan(patient_case, max_hops=max_hops)

    executed_hops: list[QueryHop] = []
    seen_chunk_ids: set[str] = set()
    aggregated_citations: list[Citation] = []
    evidence_counter = 1

    for hop in hops:
        log.info(
            "executing_query_hop",
            hop_number=hop.hop_number,
            focus=hop.focus_area,
            query=hop.query_text,
        )

        # 1. Retrieve hybrid candidates
        candidates = hybrid_search(
            query=hop.query_text,
            vector_store=vs,
            bm25_index=bm,
            dense_weight=settings.dense_weight,
            sparse_weight=settings.sparse_weight,
            top_k=settings.top_k_retrieval,
        )

        # 2. Rerank
        ranked = rerank(
            query=hop.query_text,
            candidates=candidates,
            top_k=min(3, settings.top_k_rerank),
        )

        # 3. Build citations for this hop
        hop_citations = build_citations(ranked)

        # 4. Formulate intermediate insight
        top_titles = [c.title for c in hop_citations if c.title]
        if hop.focus_area == "symptom_etiology":
            insight = f"Primary literature emphasizes syndromes associated with: {', '.join(top_titles[:2]) or 'respiratory and cardiovascular etiologies'}."
        elif hop.focus_area == "biomarker_correlation":
            insight = f"Laboratory evidence correlates biomarker elevations with inflammatory/infectious severity and acute phase response."
        else:
            insight = f"Differential literature highlights rule-outs, severity scoring criteria, and emergent exclusions."

        hop.intermediate_insight = insight
        hop.citations = hop_citations
        executed_hops.append(hop)

        # 5. Aggregate unique citations
        for cit in hop_citations:
            identifier = cit.chunk_id or cit.content[:60]
            if identifier not in seen_chunk_ids:
                seen_chunk_ids.add(identifier)
                # Re-index with hop tag
                cit_copy = cit.model_copy()
                cit_copy.source_id = f"E{evidence_counter}"
                cit_copy.section = f"Hop {hop.hop_number}: {hop.focus_area.replace('_', ' ').title()}"
                aggregated_citations.append(cit_copy)
                evidence_counter += 1

    synthesis = (
        f"Multi-hop retrieval executed across {len(executed_hops)} investigative stages, "
        f"accumulating {len(aggregated_citations)} evidence passages spanning syndrome etiology, "
        f"biomarker correlation, and clinical rule-out criteria."
    )

    return QueryPlanResult(
        case_id=patient_case.get("case_id", ""),
        hops=executed_hops,
        aggregated_citations=aggregated_citations,
        query_synthesis=synthesis,
        total_hops=len(executed_hops),
    )
