"""
End-to-End integration test suite for Phase 2:
Multi-Agent Agentic RAG Diagnostic Copilot & Medical Vision.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from graph.state import DiagnosticState
from graph.routing import should_revise, MAX_DEBATE_ITERATIONS
from graph.workflow import run_diagnostic_workflow, build_diagnostic_graph
from vision.base import VisionAnalysisResult, VisionFinding
from vision.medical_vision import MedicalVisionService, UnavailableVisionAdapter, LocalDemoVisionAdapter


@pytest.fixture
def synthetic_patient_case() -> dict:
    """Synthetic patient encounter for Phase 2 end-to-end testing."""
    return {
        "case_id": "PT-SYNTHETIC-2026",
        "patient": {"age": 45, "sex": "M"},
        "symptoms": ["fever", "cough", "shortness of breath", "fatigue"],
        "history": ["hypertension", "type 2 diabetes"],
        "clinical_notes": "Auscultation reveals crackles over the right lower lung base.",
        "labs": [
            {"name": "WBC", "value": 14.5, "unit": "×10³/μL", "reference_range": "4.5-11.0", "is_abnormal": True},
            {"name": "CRP", "value": 85.0, "unit": "mg/L", "reference_range": "<10", "is_abnormal": True},
        ],
    }


@pytest.fixture
def dummy_cxr_image(tmp_path: Path) -> str:
    path = tmp_path / "dummy_cxr.png"
    img = Image.new("RGB", (256, 256), color=(80, 80, 80))
    img.save(path)
    return str(path)


class TestPhase2EndToEndWorkflow:
    """Comprehensive acceptance test suite for Phase 2 requirements."""

    def test_workflow_execution_without_image(self, synthetic_patient_case: dict):
        """Workflow must complete cleanly in image-unavailable mode."""
        final_state = run_diagnostic_workflow(
            patient_case=synthetic_patient_case,
            image_path=None,
        )

        assert "final_report" in final_state
        rep = final_state["final_report"]

        # Check required 9-section structure
        assert "title" in rep
        assert rep["title"] == "Clinical Decision Support Report"
        assert "patient_summary" in rep
        assert "key_clinical_findings" in rep
        assert "imaging_findings" in rep
        assert "agent_assessments" in rep
        assert "differential_considerations" in rep
        assert "evidence_sources" in rep
        assert "critic_findings" in rep
        assert "missing_information" in rep
        assert "suggested_clinical_questions" in rep
        assert "safety_disclaimer" in rep

        # Mandatory safety disclaimer wording verification
        required_disclaimer = (
            "This system is a research/educational clinical decision-support prototype and "
            "does not provide a confirmed medical diagnosis or replace a qualified healthcare professional."
        )
        assert rep["safety_disclaimer"] == required_disclaimer

        # Verify no fake medical image findings were produced
        rad_findings = rep["imaging_findings"].get("findings", [])
        assert len(rad_findings) == 0

        # Verify agent logs and iteration limits
        assert len(final_state["agent_logs"]) >= 5
        assert 1 <= final_state["iteration_count"] <= 3

    def test_workflow_execution_with_image(self, synthetic_patient_case: dict, dummy_cxr_image: str):
        """Workflow must process image or report controlled unavailability."""
        final_state = run_diagnostic_workflow(
            patient_case=synthetic_patient_case,
            image_path=dummy_cxr_image,
        )

        assert "final_report" in final_state
        rep = final_state["final_report"]
        assert "imaging_findings" in rep
        img_info = rep["imaging_findings"]
        assert "modality" in img_info
        assert "overall_impression" in img_info

        # Verify specialist has differential considerations grounded in evidence
        diffs = rep["differential_considerations"]
        assert len(diffs) > 0
        for d in diffs:
            assert "condition" in d
            assert "supporting_findings" in d
            assert "contradicting_findings" in d
            assert "evidence" in d
            assert "uncertainty" in d

    def test_critic_debate_loop_hard_limit(self):
        """Debate loop must terminate at iteration 3 without infinite recursion."""
        state_at_limit: DiagnosticState = {
            "critic_feedback": {"revision_required": True, "missing_evidence": ["Extra data"]},
            "iteration_count": 3,
        }
        assert should_revise(state_at_limit) == "synthesize"

        state_under_limit: DiagnosticState = {
            "critic_feedback": {"revision_required": True, "missing_evidence": ["Extra data"]},
            "iteration_count": 2,
        }
        assert should_revise(state_under_limit) == "retrieve_again"

    def test_vision_unavailable_mode_produces_no_fake_findings(self, tmp_path: Path):
        """When vision provider credentials are missing, system returns controlled unavailability."""
        test_img = tmp_path / "test.png"
        Image.new("RGB", (100, 100), color=50).save(test_img)

        adapter = UnavailableVisionAdapter(reason="Credentials not configured.")
        service = MedicalVisionService(adapter=adapter)
        result = service.analyze(test_img)

        assert isinstance(result, VisionAnalysisResult)
        assert len(result.findings) == 0
        assert "Image analysis unavailable" in result.overall_impression
        assert result.model_used == "unavailable"
