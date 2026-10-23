"""
Tests for Similar Patient Retrieval and Case-Based Reasoning — Phase 3.
"""

from __future__ import annotations

import pytest
from patient.similar_patients import (
    find_similar_patients,
    get_reference_cohort,
    SimilarPatientResponse,
)


@pytest.fixture
def mock_pneumonia_case() -> dict:
    return {
        "case_id": "TEST-SIM-001",
        "patient": {"age": 49, "sex": "M"},
        "symptoms": ["productive cough", "fever", "chills", "pleuritic chest pain"],
        "history": ["hypertension"],
        "labs": [
            {"name": "WBC", "value": 15.8, "unit": "10^3/uL", "is_abnormal": True},
            {"name": "CRP", "value": 110.0, "unit": "mg/L", "is_abnormal": True},
        ],
    }


def test_reference_cohort_loading():
    cohort = get_reference_cohort()
    assert len(cohort) >= 6
    case_ids = [c.case_id for c in cohort]
    assert "REF-PNEUM-01" in case_ids
    assert "REF-ACS-02" in case_ids


def test_find_similar_patients_ranking(mock_pneumonia_case: dict):
    res = find_similar_patients(mock_pneumonia_case, top_k=3)
    assert isinstance(res, SimilarPatientResponse)
    assert len(res.matches) == 3

    top_match = res.matches[0]
    # Pneumonia case should match REF-PNEUM-01 top
    assert "pneumonia" in top_match.confirmed_diagnosis.lower()
    assert top_match.similarity_score > 0.5
    assert len(top_match.matched_symptoms) > 0
    assert len(top_match.key_discriminant_pearls) > 0
    assert len(top_match.clinical_takeaway) > 10
