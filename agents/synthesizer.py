"""
Final Synthesizer Agent — Phase 2.

Compiles the comprehensive, structured 9-section Clinical Decision Support Report
from all specialist agents, imaging findings, evidence citations, and critic feedback.
"""

from __future__ import annotations

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import Any
from graph.state import DiagnosticState
from logger import get_logger

log = get_logger(__name__)

DISCLAIMER_TEXT = (
    "This system is a research/educational clinical decision-support prototype and "
    "does not provide a confirmed medical diagnosis or replace a qualified healthcare professional."
)


def synthesizer_node(state: DiagnosticState) -> dict[str, Any]:
    """LangGraph node for Final Synthesizer Agent."""
    log.info("synthesizer_agent_started")
    logs = list(state.get("agent_logs", []))

    patient_case = state.get("patient_case", {})
    gp_assessment = state.get("gp_assessment", {})
    radiology_assessment = state.get("radiology_assessment", {})
    specialist_assessments = state.get("specialist_assessments", {})
    evidence = state.get("retrieved_evidence", [])
    critic_feedback = state.get("critic_feedback", {})

    # 1. Patient Summary
    patient_summary = gp_assessment.get("patient_summary") or (
        f"Patient case: {patient_case.get('patient', {}).get('age', 'Unknown')}yo "
        f"{patient_case.get('patient', {}).get('sex', 'Unknown')}, "
        f"presenting with {', '.join(patient_case.get('symptoms', [])) or 'unspecified symptoms'}."
    )

    # 2. Key Clinical Findings
    key_findings = []
    if patient_case.get("symptoms"):
        key_findings.append(f"Symptoms: {', '.join(patient_case['symptoms'])}")
    if patient_case.get("history"):
        key_findings.append(f"Relevant History: {', '.join(patient_case['history'])}")
    for lab in patient_case.get("labs", []):
        if lab.get("is_abnormal"):
            key_findings.append(f"Abnormal Lab: {lab.get('name')} = {lab.get('value')} {lab.get('unit')} (Ref: {lab.get('reference_range')})")

    # 3. Imaging Findings
    image_findings = radiology_assessment.get("findings", [])

    # 4. Agent Assessments
    cardio_spec = specialist_assessments.get("cardiopulmonary", {})

    # 5. Differential Considerations
    raw_differentials = cardio_spec.get("primary_considerations", [])
    if not raw_differentials:
        # Fall back to GP hypotheses
        for h in gp_assessment.get("initial_hypotheses", []):
            raw_differentials.append({
                "condition": h.get("condition", "Clinical Syndrome"),
                "supporting_evidence": [h.get("clinical_rationale", "Presentation factors")],
                "contradicting_evidence": [],
                "uncertainty": "moderate",
                "source_ids": [e.get("source_id") for e in evidence[:2]],
            })

    # Standardize differential consideration objects with required schema
    differentials = []
    for d in raw_differentials:
        sup = d.get("supporting_findings") or d.get("supporting_evidence") or []
        contra = d.get("contradicting_findings") or d.get("contradicting_evidence") or []
        sids = d.get("evidence") or d.get("source_ids") or []
        differentials.append({
            "condition": d.get("condition", "Clinical Syndrome"),
            "supporting_findings": sup,
            "supporting_evidence": sup,
            "contradicting_findings": contra,
            "contradicting_evidence": contra,
            "evidence": sids,
            "source_ids": sids,
            "uncertainty": d.get("uncertainty", "moderate"),
        })

    # 6. Citations / Evidence Sources
    citations = evidence

    # 7. Critic / Verification Findings
    critic_findings = {
        "supported_claims": critic_feedback.get("supported_claims", []),
        "unsupported_claims": critic_feedback.get("unsupported_claims", []),
        "contradictions": critic_feedback.get("contradictions", []),
        "missing_information": critic_feedback.get("missing_evidence", []),
        "summary": critic_feedback.get("critic_summary", "Audit completed."),
    }

    # 8. Missing Information
    missing_info = critic_feedback.get("missing_evidence") or gp_assessment.get("information_gaps") or [
        "Serial clinical observations",
        "Targeted diagnostic follow-up",
    ]

    # 9. Suggested Clinical Questions
    suggested_questions = [
        "What are the serial inflammatory or cardiac biomarker trends over a 12-24 hour window?",
        "Are there localized respiratory auscultation signs (e.g. crackles, bronchial breath sounds)?",
        "Does clinical status or pulse oximetry indicate supplemental oxygen or acute monitoring requirements?",
    ]
    if cardio_spec.get("diagnostic_recommendations"):
        suggested_questions.extend(cardio_spec["diagnostic_recommendations"])

    # Assemble Full 9-Section Clinical Decision Support Report
    final_report = {
        "title": "Clinical Decision Support Report",
        "patient_summary": patient_summary,
        "key_clinical_findings": key_findings,
        "imaging_findings": {
            "modality": radiology_assessment.get("image_modality", "None"),
            "technical_quality": radiology_assessment.get("technical_quality", "N/A"),
            "model_used": radiology_assessment.get("model_used", "N/A"),
            "overall_impression": radiology_assessment.get("overall_impression", "No imaging study available."),
            "findings": image_findings,
            "limitations": radiology_assessment.get("limitations", []),
        },
        "agent_assessments": {
            "general_physician": gp_assessment,
            "specialist": cardio_spec,
            "radiologist": radiology_assessment,
        },
        "differential_considerations": differentials,
        "evidence_sources": citations,
        "evidence_citations": citations,
        "critic_findings": critic_findings,
        "critic_verification_findings": critic_findings,
        "missing_information": missing_info,
        "suggested_clinical_questions": suggested_questions,
        "suggested_next_questions": suggested_questions,
        "safety_disclaimer": DISCLAIMER_TEXT,
    }

    # Phase 3 Enhancements: Confidence Calibration, Hallucination Audit, Similar Patients
    try:
        from evaluation.confidence_calibrator import calibrate_differential_confidence
        calib_res = calibrate_differential_confidence(
            differentials=differentials,
            critic_feedback=critic_feedback,
            citations=citations,
            missing_info=missing_info,
        )
        final_report["confidence_calibration"] = calib_res.model_dump()
    except Exception as e:
        log.warning("synthesizer_calibration_failed", error=str(e))

    try:
        from evaluation.hallucination_detector import audit_report_hallucinations
        audit_res = audit_report_hallucinations(
            patient_case=patient_case,
            report=final_report,
            citations=citations,
            image_findings=image_findings,
        )
        final_report["faithfulness_audit"] = audit_res.model_dump()
    except Exception as e:
        log.warning("synthesizer_audit_failed", error=str(e))

    try:
        from patient.similar_patients import find_similar_patients
        similar_res = find_similar_patients(patient_case=patient_case, top_k=3)
        final_report["similar_cases"] = similar_res.model_dump()
    except Exception as e:
        log.warning("synthesizer_similar_cases_failed", error=str(e))

    logs.append({
        "agent": "Final Synthesizer",
        "action": "Synthesized Clinical Decision Support Report with Phase 3 Calibration & Audit",
    })

    return {
        "final_report": final_report,
        "agent_logs": logs,
        "calibration": final_report.get("confidence_calibration", {}),
        "hallucination_audit": final_report.get("faithfulness_audit", {}),
        "similar_patients": final_report.get("similar_cases", {}).get("matches", []),
    }
