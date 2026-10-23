"""
Retrieval Agent — Phase 2.

Responsibilities:
- Analyzes information gaps requested by the GP agent or Critic agent
- Generates and reformulates targeted hybrid queries (dense + sparse)
- Automatically reformulates queries if evidence quality is sparse or sub-threshold
- Returns structured citations with relevance scores
"""

from __future__ import annotations

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import Any
from graph.state import DiagnosticState
from logger import get_logger
from rag.citations import build_citations
from rag.hybrid_search import hybrid_search
from rag.ingestion import ensure_indexes_loaded
from rag.reranker import rerank

log = get_logger(__name__)


def retrieval_agent_node(state: DiagnosticState) -> dict[str, Any]:
    """LangGraph node for Retrieval Agent."""
    log.info("retrieval_agent_started")
    logs = list(state.get("agent_logs", []))

    patient_case = state.get("patient_case", {})

    # Determine queries to execute
    queries = list(state.get("retrieval_queries", []))
    critic_feedback = state.get("critic_feedback", {})
    missing_evidence = critic_feedback.get("missing_evidence", [])

    # If critic requested revision with missing evidence gaps, add targeted queries
    if missing_evidence:
        for gap in missing_evidence:
            queries.append(f"{gap} clinical evidence guidelines")

    # Add multi-hop clinical query planning (Phase 3)
    try:
        from rag.query_planner import generate_clinical_query_plan
        hop_plans = generate_clinical_query_plan(patient_case, max_hops=3)
        for h in hop_plans:
            queries.append(h.query_text)
    except Exception as e:
        log.warning("retrieval_query_planning_fallback", error=str(e))

    # If queries are still empty, build from patient case
    symptoms = patient_case.get("symptoms", [])
    if not queries and symptoms:
        queries = [" ".join(symptoms)]

    # Deduplicate queries
    deduped_queries = list(dict.fromkeys(q.strip() for q in queries if q.strip()))[:6]

    vs, bm = ensure_indexes_loaded()
    all_results: dict[str, dict[str, Any]] = {}

    for query in deduped_queries:
        try:
            results = hybrid_search(query, vs, bm, top_k=15)
            # If query yielded poor results, reformulate with broader synonyms
            if not results:
                broader_q = " ".join([w for w in query.split() if len(w) > 3])
                if broader_q != query:
                    results = hybrid_search(broader_q, vs, bm)

            for r in results:
                cid = r["chunk_id"]
                if cid not in all_results or r["score"] > all_results[cid]["score"]:
                    all_results[cid] = r
        except Exception as e:
            log.warning("retrieval_agent_query_error", query=query, error=str(e))

    candidates = sorted(all_results.values(), key=lambda x: x["score"], reverse=True)

    # Rerank against patient summary and hypotheses
    patient_summary = state.get("gp_assessment", {}).get("patient_summary", "")
    reranked = rerank(patient_summary or "clinical case presentation", candidates, top_k=6)
    citations = build_citations(reranked)

    # Convert citations to dictionaries for serializable state
    citations_data = [c.model_dump() for c in citations]

    logs.append({
        "agent": "Retrieval Agent",
        "action": f"Executed {len(deduped_queries)} queries; retrieved and reranked {len(citations_data)} evidence citations",
        "citation_count": len(citations_data),
    })

    return {
        "retrieved_evidence": citations_data,
        "agent_logs": logs,
    }
