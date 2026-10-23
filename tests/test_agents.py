"""
Tests for individual specialist agents and LangGraph workflow — Phase 2.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from agents.critic_agent import critic_agent_node
from agents.gp_agent import gp_agent_node
from agents.radiology_agent import radiology_agent_node
from agents.retrieval_agent import retrieval_agent_node
from agents.specialist_agent import specialist_agent_node
from agents.synthesizer import synthesizer_node
from graph.routing import should_revise
from graph.state import DiagnosticState
from graph.workflow import run_diagnostic_workflow


@pytest.fixture
def mock_patient_case() -> dict:
    return {
        "case_id": "TEST-AGENTS-001",
        "patient": {"age": 58, "sex": "M"},
        "symptoms": ["productive cough", "fever", "dyspnea"],
        "history": ["hypertension", "former smoker"],
        "labs": [
            {"name": "WBC", "value": 14.8, "unit": "10^3/uL", "is_abnormal": True, "reference_range": "4.5-11.0"},
            {"name": "CRP", "value": 72.0, "unit": "mg/L", "is_abnormal": True, "reference_range": "<10"},
        ],
        "clinical_notes": "Auscultation reveals crackles over the right lower lung zone.",
    }


@pytest.fixture
def test_image_path(tmp_path: Path) -> str:
    path = tmp_path / "test_cxr.png"
    img = Image.new("RGB", (256, 256), color=(80, 80, 80))
    img.save(path)
    return str(path)


class TestAgentsIndependently:
    """Test each agent node in isolation."""

    def test_gp_agent_node(self, mock_patient_case: dict):
        state: DiagnosticState = {"patient_case": mock_patient_case, "agent_logs": []}
        out = gp_agent_node(state)
        assert "gp_assessment" in out
        assert len(out.get("hypotheses", [])) > 0
        assert len(out.get("retrieval_queries", [])) > 0
        assert len(out.get("agent_logs", [])) == 1

    def test_retrieval_agent_node(self, mock_patient_case: dict):
        state: DiagnosticState = {
            "patient_case": mock_patient_case,
            "retrieval_queries": ["pneumonia clinical guidelines", "elevated WBC"],
            "agent_logs": [],
        }
        out = retrieval_agent_node(state)
        assert "retrieved_evidence" in out
        assert len(out["retrieved_evidence"]) > 0
        assert out["retrieved_evidence"][0]["source_id"] == "E1"

    def test_radiology_agent_without_image(self, mock_patient_case: dict):
        state: DiagnosticState = {
            "patient_case": mock_patient_case,
            "image_path": None,
            "agent_logs": [],
        }
        out = radiology_agent_node(state)
        assert out["image_findings"] == []
        assert out["radiology_assessment"]["status"] == "no_image_provided"

    def test_radiology_agent_with_image(self, mock_patient_case: dict, test_image_path: str):
        state: DiagnosticState = {
            "patient_case": mock_patient_case,
            "image_path": test_image_path,
            "agent_logs": [],
            "gp_assessment": {"patient_summary": "58yo with fever and cough"},
        }
        out = radiology_agent_node(state)
        assert "image_findings" in out
        assert out["radiology_assessment"]["status"] in ("analyzed", "unavailable")

    def test_specialist_agent_node(self, mock_patient_case: dict):
        state: DiagnosticState = {
            "patient_case": mock_patient_case,
            "retrieved_evidence": [{"source_id": "E1", "title": "Pneumonia", "content": "CAP guidelines"}],
            "image_findings": [{"finding": "right lower lobe opacity"}],
            "gp_assessment": {"patient_summary": "Summary"},
            "agent_logs": [],
        }
        out = specialist_agent_node(state)
        assert "specialist_assessments" in out
        assert "cardiopulmonary" in out["specialist_assessments"]

    def test_critic_agent_node(self, mock_patient_case: dict):
        state: DiagnosticState = {
            "patient_case": mock_patient_case,
            "retrieved_evidence": [{"source_id": "E1", "title": "Pneumonia", "content": "CAP"}],
            "specialist_assessments": {
                "cardiopulmonary": {
                    "primary_considerations": [
                        {"condition": "Pneumonia", "source_ids": ["E1"]}
                    ]
                }
            },
            "agent_logs": [],
            "iteration_count": 0,
        }
        out = critic_agent_node(state)
        assert "critic_feedback" in out
        assert "supported_claims" in out["critic_feedback"]
        assert "revision_required" in out["critic_feedback"]
        assert out["iteration_count"] == 1

    def test_synthesizer_node(self, mock_patient_case: dict):
        state: DiagnosticState = {
            "patient_case": mock_patient_case,
            "gp_assessment": {"patient_summary": "Summary"},
            "radiology_assessment": {"image_modality": "CXR", "findings": []},
            "specialist_assessments": {"cardiopulmonary": {"primary_considerations": []}},
            "retrieved_evidence": [{"source_id": "E1", "title": "Title", "content": "Text"}],
            "critic_feedback": {"supported_claims": ["Claim 1"]},
            "agent_logs": [],
        }
        out = synthesizer_node(state)
        assert "final_report" in out
        rep = out["final_report"]
        assert "title" in rep
        assert "patient_summary" in rep
        assert "key_clinical_findings" in rep
        assert "imaging_findings" in rep
        assert "agent_assessments" in rep
        assert "differential_considerations" in rep
        assert "evidence_citations" in rep
        assert "critic_findings" in rep
        assert "suggested_next_questions" in rep
        assert "safety_disclaimer" in rep


class TestLangGraphWorkflow:
    """Test full LangGraph execution."""

    def test_routing_logic(self):
        # Case 1: revision required under limit
        state1: DiagnosticState = {
            "critic_feedback": {"revision_required": True},
            "iteration_count": 1,
        }
        assert should_revise(state1) == "retrieve_again"

        # Case 2: revision required at limit 3 -> terminates
        state2: DiagnosticState = {
            "critic_feedback": {"revision_required": True},
            "iteration_count": 3,
        }
        assert should_revise(state2) == "synthesize"

        # Case 3: no revision required
        state3: DiagnosticState = {
            "critic_feedback": {"revision_required": False},
            "iteration_count": 1,
        }
        assert should_revise(state3) == "synthesize"

    def test_full_graph_execution(self, mock_patient_case: dict, test_image_path: str):
        final_state = run_diagnostic_workflow(
            patient_case=mock_patient_case,
            image_path=test_image_path,
        )
        assert "final_report" in final_state
        assert "agent_logs" in final_state
        assert len(final_state["agent_logs"]) >= 5
        assert final_state["iteration_count"] >= 1
        assert final_state["iteration_count"] <= 3
