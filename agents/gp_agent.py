"""
General Physician (GP) Agent — Phase 2.

Responsibilities:
- Synthesize patient demographics, symptoms, and vital signs
- Identify major presenting clinical syndromes and risk factors
- Formulate initial differential hypotheses
- Identify information gaps and formulate targeted retrieval requests
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

GP_SYSTEM_PROMPT = """You are a board-certified General Physician (GP) AI agent in a clinical decision support system.
Your role is to assess the raw patient case, categorize symptoms, identify high-risk indicators,
formulate preliminary clinical hypotheses, and identify specific knowledge gaps that require literature retrieval.

CRITICAL SAFETY RULES:
1. NEVER provide a definitive diagnosis.
2. Use phrases like "primary clinical concern", "differential consideration", "warrants investigation".
3. NEVER prescribe medications or dosages.
4. Output ONLY valid JSON matching the schema below.

JSON Output Schema:
{
    "patient_summary": "Concise summary of demographics and presentation",
    "major_symptoms": ["symptom 1", "symptom 2"],
    "risk_factors": ["risk factor 1"],
    "initial_hypotheses": [
        {
            "condition": "Condition name",
            "clinical_rationale": "Why this is considered",
            "priority": "high|moderate|low"
        }
    ],
    "information_gaps": ["Specific clinical or lab knowledge needed"],
    "recommended_search_queries": ["Targeted medical literature query 1", "query 2"]
}
"""


def gp_agent_node(state: DiagnosticState) -> dict[str, Any]:
    """LangGraph node for General Physician Agent."""
    log.info("gp_agent_started")
    patient_case = state.get("patient_case", {})
    logs = list(state.get("agent_logs", []))

    age = patient_case.get("patient", {}).get("age", "Unknown")
    sex = patient_case.get("patient", {}).get("sex", "Unknown")
    symptoms = patient_case.get("symptoms", [])
    history = patient_case.get("history", [])
    labs = patient_case.get("labs", [])
    clinical_notes = patient_case.get("clinical_notes", "")

    # Format prompt
    case_summary = (
        f"Patient: {age}-year-old {sex}\n"
        f"Symptoms: {', '.join(symptoms) if symptoms else 'None documented'}\n"
        f"Medical History: {', '.join(history) if history else 'None documented'}\n"
        f"Laboratory Results: {json.dumps(labs)}\n"
        f"Clinical Notes: {clinical_notes or 'None'}"
    )

    assessment: dict[str, Any] = {}
    try:
        llm = get_llm_provider()
        resp = llm.generate_json(
            prompt=f"Assess this patient presentation:\n\n{case_summary}",
            system_prompt=GP_SYSTEM_PROMPT,
        )
        if not resp.get("parse_error"):
            assessment = resp
    except Exception as e:
        log.warning("gp_agent_llm_fallback", error=str(e))

    # Deterministic heuristic fallback if LLM unavailable or failed
    if not assessment:
        hypotheses = []
        sym_text = " ".join(symptoms).lower() + " " + clinical_notes.lower()
        if "cough" in sym_text or "fever" in sym_text or "dyspnea" in sym_text:
            hypotheses.append({
                "condition": "Lower Respiratory Tract Infection / Pneumonia",
                "clinical_rationale": "Presentation with respiratory symptoms, fever, or inflammatory response.",
                "priority": "high",
            })
        if "chest pain" in sym_text or any(l.get("name", "").lower() == "troponin" and l.get("is_abnormal") for l in labs):
            hypotheses.append({
                "condition": "Acute Coronary Syndrome / Myocardial Ischemia",
                "clinical_rationale": "Chest pain with cardiac risk factors or biomarker elevation.",
                "priority": "high",
            })
        if not hypotheses:
            hypotheses.append({
                "condition": "Undifferentiated Acute Systemic Illness",
                "clinical_rationale": "Nonspecific presentation requiring comprehensive investigation.",
                "priority": "moderate",
            })

        queries = [f"{s} clinical guidelines differential" for s in symptoms[:3]]
        if not queries:
            queries = ["clinical decision support differential diagnosis"]

        assessment = {
            "patient_summary": f"{age}-year-old {sex} presenting with {', '.join(symptoms) or 'unspecified symptoms'}.",
            "major_symptoms": symptoms,
            "risk_factors": history,
            "initial_hypotheses": hypotheses,
            "information_gaps": ["Diagnostic criteria and evidence-based guideline recommendations"],
            "recommended_search_queries": queries,
        }

    logs.append({
        "agent": "General Physician Agent",
        "action": "Generated clinical summary, risk profile, and initial hypotheses",
        "hypotheses_count": len(assessment.get("initial_hypotheses", [])),
    })

    return {
        "gp_assessment": assessment,
        "hypotheses": assessment.get("initial_hypotheses", []),
        "retrieval_queries": assessment.get("recommended_search_queries", []),
        "agent_logs": logs,
    }
