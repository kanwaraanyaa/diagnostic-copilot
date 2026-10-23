"""
Tests for Phase 3 FastAPI Endpoints.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


@pytest.fixture
def sample_payload() -> dict:
    return {
        "patient_id": "TEST-PHASE3-API",
        "age": 50,
        "sex": "M",
        "symptoms": ["cough", "fever", "dyspnea"],
        "history": ["hypertension"],
        "labs": [{"name": "WBC", "value": 15.2, "unit": "10^3/uL", "is_abnormal": True}],
    }


def test_phase3_query_plan_endpoint(sample_payload: dict):
    resp = client.post("/api/phase3/query-plan?max_hops=3", json=sample_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_hops"] == 3
    assert len(data["hops"]) == 3
    assert len(data["aggregated_citations"]) > 0


def test_phase3_similar_patients_endpoint(sample_payload: dict):
    resp = client.post("/api/phase3/similar-patients?top_k=3", json=sample_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["matches"]) == 3
    assert "pneumonia" in data["matches"][0]["confirmed_diagnosis"].lower()


def test_phase3_evidence_graph_endpoint(sample_payload: dict):
    resp = client.post("/api/phase3/evidence-graph", json=sample_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_nodes"] > 0
    assert data["total_edges"] > 0


def test_phase3_hallucination_audit_endpoint():
    payload = {
        "patient_case": {"case_id": "C1", "symptoms": ["cough", "fever"]},
        "report": {
            "patient_summary": "Patient presenting with cough and fever.",
            "differential_considerations": [{"condition": "Pneumonia", "supporting_evidence": ["cough"]}],
        },
        "citations": [{"source_id": "E1", "title": "Pneumonia", "content": "Pneumonia criteria"}],
    }
    resp = client.post("/api/phase3/hallucination-audit", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "faithfulness_score" in data


def test_phase3_calibration_endpoint():
    payload = {
        "differentials": [{"condition": "Pneumonia", "uncertainty": "low"}],
        "critic_feedback": {"contradictions": []},
    }
    resp = client.post("/api/phase3/calibration", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "expected_calibration_error" in data
    assert len(data["conditions"]) == 1


def test_phase3_benchmark_cases_catalog():
    resp = client.get("/api/phase3/benchmark/cases")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_cases"] == 50
    assert len(data["cases"]) == 50


def test_phase3_benchmark_latest_endpoint():
    resp = client.get("/api/phase3/benchmark/latest")
    assert resp.status_code == 200
    data = resp.json()
    assert "top_1_accuracy" in data
