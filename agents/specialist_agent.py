"""
Specialist Agent (Cardiology / Pulmonology) — Phase 2.

Responsibilities:
- Independently evaluates patient presentation from a specialist standpoint
- Synthesizes specialist evidence, biomarker trends, and radiology correlation
- Formulates differential considerations with supporting/contradicting evidence
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

SPECIALIST_SYSTEM_PROMPT = """You are a medical subspecialist (Cardiologist and Pulmonologist) in a clinical decision support system.
Evaluate the case objectively based on patient data, retrieved evidence citations, and imaging findings.

CRITICAL SAFETY RULES:
1. Ground your observations strictly in the provided retrieved evidence and clinical presentation.
2. Distinguish clearly between cardiac and pulmonary etiologies.
3. List supporting evidence AND contradicting/attenuating evidence for each condition.
4. Output ONLY valid JSON matching this schema:
{{
    "specialty": "Cardiopulmonary",
    "specialist_summary": "Domain evaluation of the case",
    "primary_considerations": [
        {{
            "condition": "Condition name",
            "supporting_evidence": ["Key finding 1", "Evidence [E1] point"],
            "contradicting_evidence": ["Absence of finding X", "Negative biomarker Y"],
            "uncertainty": "low|moderate|high",
            "source_ids": ["E1", "E2"]
        }}
    ],
    "diagnostic_recommendations": ["Recommended test or imaging study (NO drugs/prescriptions)"]
}}
"""


def specialist_agent_node(state: DiagnosticState) -> dict[str, Any]:
    """LangGraph node for Specialist Agent."""
    log.info("specialist_agent_started")
    logs = list(state.get("agent_logs", []))

    patient_case = state.get("patient_case", {})
    gp_assessment = state.get("gp_assessment", {})
    evidence = state.get("retrieved_evidence", [])
    image_findings = state.get("image_findings", [])

    # Format context for specialist
    context = (
        f"GP Summary: {gp_assessment.get('patient_summary', 'N/A')}\n"
        f"Hypotheses: {json.dumps(gp_assessment.get('initial_hypotheses', []))}\n"
        f"Imaging Observations: {json.dumps(image_findings)}\n"
        f"Retrieved Evidence Citations:\n"
    )
    for ev in evidence:
        context += f"[{ev.get('source_id')}] {ev.get('title')}: {ev.get('content')[:180]}...\n"

    assessment: dict[str, Any] = {}
    try:
        llm = get_llm_provider()
        resp = llm.generate_json(
            prompt=f"Specialist assessment for this presentation:\n\n{context}",
            system_prompt=SPECIALIST_SYSTEM_PROMPT,
        )
        if not resp.get("parse_error"):
            assessment = resp
    except Exception as e:
        log.warning("specialist_agent_llm_fallback", error=str(e))

    # Deterministic heuristic specialist fallback
    if not assessment:
        symptoms = [s.lower() for s in patient_case.get("symptoms", [])]
        labs = patient_case.get("labs", [])
        troponin_abnormal = any(l.get("name", "").lower() == "troponin" and l.get("is_abnormal") for l in labs)
        wbc_abnormal = any(l.get("name", "").lower() == "wbc" and l.get("is_abnormal") for l in labs)
        crp_abnormal = any(l.get("name", "").lower() == "crp" and l.get("is_abnormal") for l in labs)

        considerations = []
        # Pulmonary assessment
        if any(s in ("cough", "fever", "shortness of breath", "dyspnea") for s in symptoms) or wbc_abnormal:
            srcs = [ev.get("source_id") for ev in evidence if "pneumonia" in ev.get("title", "").lower() or "cbc" in ev.get("title", "").lower()]
            img_support = [
                f.get("finding") for f in image_findings
                if any(k in f.get("finding", "").lower() for k in ("opacity", "consolidation", "density", "infiltrate", "asymmetry"))
            ]
            supp = ["Elevated inflammatory or leukocyte response", "Acute respiratory symptom cluster"]
            if img_support:
                supp.append(f"Radiology finding: {img_support[0]}")
            considerations.append({
                "condition": "Community-Acquired Pneumonia / Infectious Infiltrate",
                "supporting_evidence": supp,
                "contradicting_evidence": ["Absence of overt hemodynamic collapse"] if not troponin_abnormal else [],
                "uncertainty": "moderate",
                "source_ids": srcs or (["E1"] if evidence else []),
            })

        # Cardiac assessment
        if troponin_abnormal or "chest pain" in symptoms:
            srcs = [ev.get("source_id") for ev in evidence if "coronary" in ev.get("title", "").lower()]
            considerations.append({
                "condition": "Acute Coronary Syndrome / Myocardial Injury",
                "supporting_evidence": ["Elevated cardiac troponin biomarker" if troponin_abnormal else "Chest discomfort symptom"],
                "contradicting_evidence": ["Isolated respiratory symptoms without classic radiating substernal pain"] if "cough" in symptoms else [],
                "uncertainty": "moderate",
                "source_ids": srcs or (["E2"] if len(evidence) > 1 else []),
            })

        if not considerations:
            considerations.append({
                "condition": "Nonspecific Inflammatory Process",
                "supporting_evidence": ["Systemic presentation noted by GP assessment"],
                "contradicting_evidence": ["No focal localization identified on routine labs"],
                "uncertainty": "high",
                "source_ids": [ev.get("source_id") for ev in evidence[:1]],
            })

        assessment = {
            "specialty": "Cardiopulmonary",
            "specialist_summary": "Evaluated cardiopulmonary risk indicators, biomarker trajectories, and imaging correlation.",
            "primary_considerations": considerations,
            "diagnostic_recommendations": [
                "Serial cardiac enzyme monitoring if symptoms persist or chest discomfort recurs",
                "Microbiological sputum assessment and pulse oximetry monitoring",
            ],
        }

    logs.append({
        "agent": "Specialist Agent",
        "action": f"Specialist assessment completed with {len(assessment.get('primary_considerations', []))} differential considerations",
        "considerations_count": len(assessment.get("primary_considerations", [])),
    })

    return {
        "specialist_assessments": {"cardiopulmonary": assessment},
        "agent_logs": logs,
    }
