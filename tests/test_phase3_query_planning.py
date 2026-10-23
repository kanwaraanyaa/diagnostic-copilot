"""
Tests for Agentic Query Planning and Multi-Hop Retrieval — Phase 3.
"""

from __future__ import annotations

import pytest
from rag.query_planner import (
    QueryHop,
    QueryPlanResult,
    generate_clinical_query_plan,
    execute_multi_hop_retrieval,
)


@pytest.fixture
def mock_case() -> dict:
    return {
        "case_id": "TEST-HOP-001",
        "patient": {"age": 54, "sex": "M"},
        "symptoms": ["fever", "cough", "purulent sputum", "pleuritic chest pain"],
        "history": ["hypertension", "former smoker"],
        "labs": [
            {"name": "WBC", "value": 16.2, "unit": "10^3/uL", "is_abnormal": True},
            {"name": "CRP", "value": 95.0, "unit": "mg/L", "is_abnormal": True},
        ],
        "clinical_notes": "Right basilar crackles and fever.",
    }


def test_generate_clinical_query_plan(mock_case: dict):
    hops = generate_clinical_query_plan(mock_case, max_hops=3)
    assert len(hops) == 3

    assert hops[0].hop_number == 1
    assert hops[0].focus_area == "symptom_etiology"
    assert "cough" in hops[0].query_text.lower() or "fever" in hops[0].query_text.lower()

    assert hops[1].hop_number == 2
    assert hops[1].focus_area == "biomarker_correlation"
    assert "wbc" in hops[1].query_text.lower() or "crp" in hops[1].query_text.lower()

    assert hops[2].hop_number == 3
    assert hops[2].focus_area == "differential_exclusion"
    assert "differential" in hops[2].query_text.lower() or "complications" in hops[2].query_text.lower()


def test_execute_multi_hop_retrieval(mock_case: dict):
    plan_result = execute_multi_hop_retrieval(mock_case, max_hops=3)
    assert isinstance(plan_result, QueryPlanResult)
    assert plan_result.total_hops == 3
    assert len(plan_result.hops) == 3
    assert len(plan_result.aggregated_citations) > 0
    assert "E1" in [c.source_id for c in plan_result.aggregated_citations]
    assert any("Hop" in c.section for c in plan_result.aggregated_citations)
