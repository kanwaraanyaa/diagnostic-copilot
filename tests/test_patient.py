"""
Tests for patient normalization and validation — Phase 1.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from backend.schemas.patient import LabResult, PatientCase, PatientInfo, Sex
from patient.normalizer import normalize_patient_case, patient_case_to_prompt
from patient.validators import ValidationError, validate_image_file, validate_patient_input


# =============================================================================
# Patient Normalization Tests
# =============================================================================


class TestNormalizePatientCase:
    """Tests for normalize_patient_case()."""

    def test_basic_normalization(self):
        raw = {
            "age": 45,
            "sex": "M",
            "symptoms": "fever, cough",
            "history": "hypertension",
            "clinical_notes": "Patient presents with fever.",
            "labs": [
                {"name": "WBC", "value": 14.5, "unit": "×10³/μL", "is_abnormal": True},
            ],
        }
        case = normalize_patient_case(raw)

        assert case.patient.age == 45
        assert case.patient.sex == Sex.MALE
        assert "fever" in case.symptoms
        assert "cough" in case.symptoms
        assert len(case.labs) == 1
        assert case.labs[0].name == "WBC"
        assert case.labs[0].value == 14.5

    def test_empty_input(self):
        case = normalize_patient_case({})
        assert case.patient.sex == Sex.UNKNOWN
        assert case.symptoms == []
        assert case.labs == []

    def test_sex_normalization(self):
        for raw_sex, expected in [
            ("M", Sex.MALE),
            ("male", Sex.MALE),
            ("MALE", Sex.MALE),
            ("F", Sex.FEMALE),
            ("female", Sex.FEMALE),
            ("Other", Sex.OTHER),
            ("xyz", Sex.UNKNOWN),
        ]:
            case = normalize_patient_case({"sex": raw_sex})
            assert case.patient.sex == expected, f"Failed for '{raw_sex}'"

    def test_symptoms_from_string(self):
        case = normalize_patient_case({"symptoms": "fever, cough, headache"})
        assert len(case.symptoms) == 3
        assert "fever" in case.symptoms

    def test_symptoms_from_list(self):
        case = normalize_patient_case({"symptoms": ["fever", "cough"]})
        assert len(case.symptoms) == 2

    def test_invalid_lab_value_skipped(self):
        raw = {
            "labs": [
                {"name": "WBC", "value": "not-a-number"},
                {"name": "CRP", "value": 85.0},
            ]
        }
        case = normalize_patient_case(raw)
        assert len(case.labs) == 1
        assert case.labs[0].name == "CRP"

    def test_lab_without_name_skipped(self):
        raw = {"labs": [{"name": "", "value": 10}]}
        case = normalize_patient_case(raw)
        assert len(case.labs) == 0

    def test_patient_id_assignment(self):
        case = normalize_patient_case({"patient_id": "TEST-001"})
        assert case.case_id == "TEST-001"

    def test_auto_generated_case_id(self):
        case = normalize_patient_case({})
        assert len(case.case_id) > 0


class TestPatientCaseToPrompt:
    """Tests for patient_case_to_prompt()."""

    def test_full_case_prompt(self):
        case = PatientCase(
            patient=PatientInfo(age=45, sex=Sex.MALE),
            symptoms=["fever", "cough"],
            history=["hypertension"],
            labs=[LabResult(name="WBC", value=14.5, unit="×10³/μL", is_abnormal=True)],
            clinical_notes="Productive cough for 3 days.",
        )
        prompt = patient_case_to_prompt(case)

        assert "45-year-old" in prompt
        assert "male" in prompt
        assert "fever" in prompt
        assert "cough" in prompt
        assert "hypertension" in prompt
        assert "WBC" in prompt
        assert "ABNORMAL" in prompt
        assert "Productive cough" in prompt

    def test_minimal_case_prompt(self):
        case = PatientCase()
        prompt = patient_case_to_prompt(case)
        assert "patient" in prompt.lower()


# =============================================================================
# Validation Tests
# =============================================================================


class TestValidatePatientInput:
    """Tests for validate_patient_input()."""

    def test_full_valid_input(self):
        raw = {
            "age": 45,
            "symptoms": "fever, cough",
            "labs": [{"name": "WBC", "value": 14}],
            "clinical_notes": "Some notes.",
        }
        warnings = validate_patient_input(raw)
        assert len(warnings) == 0

    def test_missing_symptoms_warning(self):
        warnings = validate_patient_input({"age": 45})
        assert any("symptom" in w.lower() for w in warnings)

    def test_missing_labs_warning(self):
        warnings = validate_patient_input({"symptoms": "fever"})
        assert any("lab" in w.lower() for w in warnings)

    def test_invalid_age_warning(self):
        warnings = validate_patient_input({"age": -5})
        assert any("age" in w.lower() for w in warnings)

    def test_empty_input_warnings(self):
        warnings = validate_patient_input({})
        assert len(warnings) >= 2  # At least symptoms and labs warnings


class TestValidateImageFile:
    """Tests for validate_image_file()."""

    def test_valid_png(self):
        # Should not raise
        validate_image_file("test.png", file_size_bytes=1024)

    def test_valid_jpg(self):
        validate_image_file("test.jpg", file_size_bytes=1024)

    def test_invalid_extension(self):
        with pytest.raises(ValidationError):
            validate_image_file("test.bmp", file_size_bytes=1024)

    def test_file_too_large(self):
        with pytest.raises(ValidationError):
            validate_image_file("test.png", file_size_bytes=100 * 1024 * 1024)
