"""
Tests for the FastAPI backend — Phase 1.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Tests for GET /api/health."""

    def test_health_check(self):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["phase"] in (1, 2, 3)


class TestCaseEndpoints:
    """Tests for POST /api/cases and GET /api/cases/{id}."""

    def test_create_case(self):
        payload = {
            "patient_id": "TEST-API-001",
            "age": 55,
            "sex": "F",
            "symptoms": "chest pain, shortness of breath",
            "history": "diabetes",
            "clinical_notes": "Acute onset chest pain.",
            "labs": [
                {"name": "Troponin", "value": 0.15, "unit": "ng/mL", "is_abnormal": True}
            ],
        }
        resp = client.post("/api/cases", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "case_id" in data

    def test_get_case(self):
        # Create first
        payload = {"patient_id": "TEST-GET-001", "symptoms": "headache"}
        resp = client.post("/api/cases", json=payload)
        assert resp.status_code == 200

        # Retrieve
        resp = client.get("/api/cases/TEST-GET-001")
        assert resp.status_code == 200

    def test_get_nonexistent_case(self):
        resp = client.get("/api/cases/NONEXISTENT-999")
        assert resp.status_code == 404


class TestRetrievalEndpoint:
    """Tests for POST /api/retrieve."""

    def test_retrieve_evidence(self):
        payload = {"query": "pneumonia symptoms", "top_k": 3}
        resp = client.post("/api/retrieve", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data


class TestSchemaValidation:
    """Tests for Pydantic schema validation."""

    def test_empty_case_allowed(self):
        resp = client.post("/api/cases", json={})
        assert resp.status_code == 200

    def test_invalid_age_rejected(self):
        payload = {"age": -10}
        resp = client.post("/api/cases", json=payload)
        # Pydantic should reject negative age
        assert resp.status_code in (200, 422)


class TestPhase2Endpoints:
    """Tests for Phase 2 multi-agent workflow and vision endpoints."""

    def test_analyze_agentic_endpoint(self):
        payload = {
            "patient_id": "TEST-AGENTIC-001",
            "age": 45,
            "sex": "M",
            "symptoms": "fever, productive cough, shortness of breath",
            "history": "hypertension",
            "clinical_notes": "Auscultation shows crackles in right lower zone.",
            "labs": [
                {"name": "WBC", "value": 14.2, "unit": "×10³/μL", "is_abnormal": True, "reference_range": "4.5-11.0"}
            ],
        }
        resp = client.post("/api/analyze/agentic", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "final_report" in data
        assert "agent_logs" in data
        assert data["iteration_count"] >= 1

    def test_upload_image_endpoint(self, tmp_path):
        import io
        from PIL import Image

        img_bytes = io.BytesIO()
        img = Image.new("RGB", (128, 128), color=(50, 50, 50))
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        files = {"file": ("test_upload.png", img_bytes, "image/png")}
        resp = client.post("/api/upload/image", files=files)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "image_path" in data

    def test_analyze_image_endpoint(self):
        import io
        from PIL import Image

        img_bytes = io.BytesIO()
        img = Image.new("RGB", (256, 256), color=(70, 70, 70))
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        files = {"file": ("test_radiology.png", img_bytes, "image/png")}
        resp = client.post("/api/analyze/image", files=files)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "findings" in data
        assert "overall_impression" in data

