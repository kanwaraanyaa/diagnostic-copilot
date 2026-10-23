"""
Patient case normalizer — converts raw form input into a validated PatientCase.
"""

from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import Any
from uuid import uuid4

from backend.schemas.patient import (
    LabResult,
    PatientCase,
    PatientInfo,
    Sex,
)
from logger import get_logger

log = get_logger(__name__)


# ---- helpers ---------------------------------------------------------------

_SEX_MAP: dict[str, Sex] = {
    "m": Sex.MALE,
    "male": Sex.MALE,
    "f": Sex.FEMALE,
    "female": Sex.FEMALE,
    "other": Sex.OTHER,
}


def _normalize_sex(raw: str) -> Sex:
    return _SEX_MAP.get(raw.strip().lower(), Sex.UNKNOWN)


def _parse_lab(raw: dict[str, Any]) -> LabResult | None:
    """Parse a single lab-result dict, returning None on failure."""
    name = str(raw.get("name", "")).strip()
    if not name:
        return None
    try:
        value = float(raw.get("value", 0))
    except (ValueError, TypeError):
        log.warning("invalid_lab_value", name=name, raw_value=raw.get("value"))
        return None
    return LabResult(
        name=name,
        value=value,
        unit=str(raw.get("unit", "")).strip(),
        reference_range=str(raw.get("reference_range", "")).strip(),
        is_abnormal=raw.get("is_abnormal"),
    )


# ---- public API ------------------------------------------------------------

def normalize_patient_case(raw: dict[str, Any]) -> PatientCase:
    """
    Convert raw form/API input into a validated ``PatientCase``.

    Parameters
    ----------
    raw : dict
        Unstructured input with keys such as *age*, *sex*, *symptoms*,
        *history*, *clinical_notes*, *labs*, *case_description*.

    Returns
    -------
    PatientCase
        A fully validated, structured patient case.
    """
    patient_info = PatientInfo(
        age=raw.get("age"),
        sex=_normalize_sex(str(raw.get("sex", "Unknown"))),
    )

    labs: list[LabResult] = []
    for lab_raw in raw.get("labs", []):
        parsed = _parse_lab(lab_raw)
        if parsed is not None:
            labs.append(parsed)

    patient_id = str(raw.get("patient_id") or "").strip()
    case_id = patient_id if patient_id else uuid4().hex[:12]

    case = PatientCase(
        case_id=case_id,
        patient=patient_info,
        symptoms=raw.get("symptoms", []),
        history=raw.get("history", []),
        labs=labs,
        clinical_notes=str(raw.get("clinical_notes", "")),
        case_description=str(raw.get("case_description", "")),
    )

    log.info(
        "patient_case_normalized",
        case_id=case.case_id,
        symptom_count=len(case.symptoms),
        lab_count=len(case.labs),
    )
    return case


def patient_case_to_prompt(case: PatientCase) -> str:
    """
    Render a patient case as a clinical-style text block for LLM prompts.
    """
    parts: list[str] = []

    # Demographics
    demo = []
    if case.patient.age is not None:
        demo.append(f"{case.patient.age}-year-old")
    if case.patient.sex != Sex.UNKNOWN:
        demo.append(f"{'male' if case.patient.sex == Sex.MALE else 'female' if case.patient.sex == Sex.FEMALE else 'patient'}")
    else:
        demo.append("patient")
    parts.append("Patient: " + " ".join(demo))

    # Symptoms
    if case.symptoms:
        parts.append("Presenting symptoms: " + ", ".join(case.symptoms))

    # History
    if case.history:
        parts.append("Medical history: " + ", ".join(case.history))

    # Labs
    if case.labs:
        lab_strs = []
        for lab in case.labs:
            s = f"{lab.name}: {lab.value}"
            if lab.unit:
                s += f" {lab.unit}"
            if lab.is_abnormal:
                s += " (ABNORMAL)"
            lab_strs.append(s)
        parts.append("Laboratory results:\n  " + "\n  ".join(lab_strs))

    # Clinical notes
    if case.clinical_notes.strip():
        parts.append(f"Clinical notes: {case.clinical_notes.strip()}")

    # Description
    if case.case_description.strip():
        parts.append(f"Additional information: {case.case_description.strip()}")

    return "\n\n".join(parts)
