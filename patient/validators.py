"""
Input validators for patient data and uploaded files.
"""

from __future__ import annotations

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pathlib import Path
from typing import Any

from config import get_settings
from logger import get_logger

log = get_logger(__name__)


class ValidationError(Exception):
    """Raised when patient input or file validation fails."""

    def __init__(self, field: str, message: str) -> None:
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


def validate_patient_input(raw: dict[str, Any]) -> list[str]:
    """
    Return a list of warning/info messages (not hard errors) about the input.
    A completely empty case is allowed — the system will note missing data.
    """
    warnings: list[str] = []

    age = raw.get("age")
    if age is not None:
        try:
            age_int = int(age)
            if age_int < 0 or age_int > 150:
                warnings.append("Age is outside the expected range (0–150).")
        except (ValueError, TypeError):
            warnings.append("Age must be a number.")

    symptoms = raw.get("symptoms", [])
    if isinstance(symptoms, str):
        symptoms = [s.strip() for s in symptoms.split(",") if s.strip()]
    if not symptoms:
        warnings.append("No symptoms provided. Analysis may be limited.")

    labs = raw.get("labs", [])
    if not labs:
        warnings.append("No laboratory results provided.")

    notes = str(raw.get("clinical_notes", "")).strip()
    if not notes:
        warnings.append("No clinical notes provided.")

    return warnings


def validate_image_file(file_path: str | Path, file_size_bytes: int | None = None) -> None:
    """
    Validate an uploaded image file (used in Phase 2 but defined here for reuse).

    Raises
    ------
    ValidationError
        On invalid type or size.
    """
    settings = get_settings()
    path = Path(file_path)

    # Extension check
    allowed = {f".{t.strip()}" for t in settings.allowed_image_types.split(",")}
    if path.suffix.lower() not in allowed:
        raise ValidationError(
            "image",
            f"Unsupported file type '{path.suffix}'. Allowed: {', '.join(allowed)}",
        )

    # Size check
    if file_size_bytes is not None:
        max_bytes = settings.max_image_size_mb * 1024 * 1024
        if file_size_bytes > max_bytes:
            raise ValidationError(
                "image",
                f"File exceeds maximum size of {settings.max_image_size_mb} MB.",
            )
