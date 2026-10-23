"""
Tests for Hallucination Detection and Confidence Calibration — Phase 3.
"""

from __future__ import annotations

import pytest
from evaluation.confidence_calibrator import (
    CalibrationResult,
    calibrate_differential_confidence,
)
from evaluation.hallucination_detector import (
    HallucinationAuditResult,
    audit_report_hallucinations,
)


def test_hallucination_auditing():
    patient_case = {
        "case_id": "TEST-AUDIT-001",
        "symptoms": ["cough", "fever"],
        "history": ["hypertension"],
        "labs": [{"name": "WBC", "value": 15.0, "is_abnormal": True}],
    }

    report = {
        "patient_summary": "55yo male presenting with cough and fever.",
        "differential_considerations": [
            {
                "condition": "Pneumonia",
                "supporting_evidence": ["fever", "cough", "WBC"],
                "source_ids": ["E1"],
            },
            {
                "condition": "Ungrounded Fabrication",
                "supporting_evidence": ["intracranial mass", "papilledema"],  # Not in patient chart or citations
                "source_ids": ["E99"],  # Non-existent citation
            },
        ],
    }

    citations = [
        {"source_id": "E1", "title": "Pneumonia Criteria", "content": "Pneumonia presents with fever and cough."}
    ]

    result = audit_report_hallucinations(patient_case, report, citations)
    assert isinstance(result, HallucinationAuditResult)
    assert result.total_claims_audited > 0
    assert result.grounded_claims_count > 0
    assert result.ungrounded_claims_count > 0
    assert result.faithfulness_score < 100.0  # Due to ungrounded fabrication
    assert result.hallucination_rate > 0.0


def test_confidence_calibration():
    differentials = [
        {"condition": "Condition A", "uncertainty": "low"},
        {"condition": "Condition B", "uncertainty": "moderate"},
        {"condition": "Condition C", "uncertainty": "high"},
    ]

    critic_feedback = {
        "contradictions": ["Conflict detected in chest pain assessment"],
        "unsupported_claims": ["Unsupported symptom cited"],
        "missing_information": ["Serial ECG required", "Cardiac troponin trend"],
    }

    result = calibrate_differential_confidence(
        differentials=differentials,
        critic_feedback=critic_feedback,
        missing_info=["Serial ECG required", "Cardiac troponin trend"],
    )

    assert isinstance(result, CalibrationResult)
    assert len(result.conditions) == 3
    assert len(result.reliability_bins) == 5
    assert result.expected_calibration_error >= 0.0

    # Ensure penalties were applied
    cond_a = result.conditions[0]
    assert cond_a.calibrated_confidence < cond_a.raw_confidence
    assert "critic_contradiction_penalty" in cond_a.penalty_deductions
