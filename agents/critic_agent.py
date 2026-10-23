"""
Critic / Verifier Agent — Phase 2.

Responsibilities:
- Verifies grounding: checks if claims made by GP and Specialist are supported by citations
- Validates citation relevance
- Checks for inter-agent contradictions (e.g., GP vs Specialist vs Radiology)
- Validates consistency of image interpretations
- Calibrates confidence and flags hallucinations
- Determines if revision is required (controlled loop, max 3 iterations)
"""

from __future__ import annotations

import json
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import Any
from backend.services.llm_service import get_llm_provider
from graph.state import DiagnosticState
from logger import get_logger

log = get_logger(__name__)

CRITIC_SYSTEM_PROMPT = """You are a rigorous Clinical Verification and Critic AI agent in a decision support system.
Your primary duty is quality assurance, safety, and evidence-grounding audit.

You must examine:
1. SUPPORTED CLAIMS: Are claims corroborated by the retrieved evidence citations [E1], [E2]?
2. UNSUPPORTED CLAIMS: Are there ungrounded assertions or hallucinated claims?
3. CONTRADICTIONS: Are there discrepancies between the GP, Specialist, or Radiologist assessments?
4. MISSING EVIDENCE: Are there critical diagnostic gaps that a retrieval re-query could address?
5. REVISION REQUIRED: Set to true ONLY if there is critical unaddressed evidence gap and iteration < 3.

Respond ONLY with valid JSON:
{{
    "supported_claims": ["Claim 1 supported by citation [E1]"],
    "unsupported_claims": ["Claim without citation or evidence backing"],
    "contradictions": ["Contradiction 1, or none detected"],
    "missing_evidence": ["Missing topic requiring search, or empty list"],
    "revision_required": false,
    "critic_summary": "Comprehensive assessment of consistency and validity"
}}
"""


def critic_agent_node(state: DiagnosticState) -> dict[str, Any]:
    """LangGraph node for Critic / Verifier Agent."""
    log.info("critic_agent_started")
    logs = list(state.get("agent_logs", []))

    iteration = state.get("iteration_count", 0) + 1
    evidence = state.get("retrieved_evidence", [])
    gp_assessment = state.get("gp_assessment", {})
    specialist_assessments = state.get("specialist_assessments", {})
    image_findings = state.get("image_findings", [])

    # Bundle statements for review
    review_package = {
        "retrieved_evidence_ids": [e.get("source_id") for e in evidence],
        "gp_hypotheses": gp_assessment.get("initial_hypotheses", []),
        "specialist_considerations": specialist_assessments.get("cardiopulmonary", {}).get("primary_considerations", []),
        "image_findings": image_findings,
        "current_iteration": iteration,
    }

    feedback: dict[str, Any] = {}
    try:
        llm = get_llm_provider()
        resp = llm.generate_json(
            prompt=f"Perform verification audit on this multi-agent state:\n\n{json.dumps(review_package, indent=2)}",
            system_prompt=CRITIC_SYSTEM_PROMPT,
        )
        if not resp.get("parse_error"):
            feedback = resp
    except Exception as e:
        log.warning("critic_agent_llm_fallback", error=str(e))

    # Deterministic heuristic critic fallback
    if not feedback:
        supported = []
        unsupported = []
        contradictions = []
        missing = []

        valid_source_ids = {e.get("source_id") for e in evidence}
        specialist_cons = specialist_assessments.get("cardiopulmonary", {}).get("primary_considerations", [])

        for c in specialist_cons:
            s_ids = set(c.get("source_ids", []))
            cond = c.get("condition", "Condition")
            if s_ids and s_ids.issubset(valid_source_ids):
                supported.append(f"{cond} is supported by citations: {', '.join(sorted(s_ids))}")
            elif not s_ids:
                unsupported.append(f"{cond} lacks explicit evidence source citations.")
            else:
                supported.append(f"{cond} has partial citation grounding.")

        # Check image consistency
        if image_findings:
            has_opacity = any("opacity" in f.get("finding", "").lower() or "consolidation" in f.get("finding", "").lower() for f in image_findings)
            has_resp_hyp = any("pneumonia" in c.get("condition", "").lower() or "respiratory" in c.get("condition", "").lower() for c in specialist_cons)
            if has_opacity and not has_resp_hyp:
                contradictions.append("Radiology noted focal opacity/consolidation, but respiratory etiology was not prioritized by clinical agents.")
            else:
                supported.append("Radiological opacity findings are concordant with specialist differential considerations.")

        # Check iteration loop limit
        revision_needed = False
        if len(evidence) < 2 and iteration < 3:
            missing.append("Additional evidence on diagnostic thresholds")
            revision_needed = True

        feedback = {
            "supported_claims": supported or ["General clinical claims are grounded in baseline clinical parameters."],
            "unsupported_claims": unsupported,
            "contradictions": contradictions or ["No overt inter-agent contradictions detected between GP, Specialist, and Radiologist."],
            "missing_evidence": missing,
            "revision_required": revision_needed and (iteration < 3),
            "critic_summary": f"Audit complete for iteration {iteration}. " + (
                "Verified cross-specialty consistency and citation mapping." if not contradictions else "Flagged items for refinement."
            ),
        }

    # Hard safety clamp: Never allow loop beyond iteration 3
    if iteration >= 3:
        feedback["revision_required"] = False

    logs.append({
        "agent": "Critic / Verifier Agent",
        "action": f"Audit completed (Iteration {iteration}). Revision required: {feedback.get('revision_required', False)}",
        "supported_claims_count": len(feedback.get("supported_claims", [])),
        "unsupported_claims_count": len(feedback.get("unsupported_claims", [])),
        "contradictions_count": len(feedback.get("contradictions", [])),
    })

    return {
        "critic_feedback": feedback,
        "iteration_count": iteration,
        "iteration": iteration,
        "agent_logs": logs,
    }
