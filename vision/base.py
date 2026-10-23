"""
Base interfaces and data schemas for Medical Vision Service — Phase 2.
"""

from __future__ import annotations

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

from backend.schemas.patient import UncertaintyLevel


@dataclass
class VisionFinding:
    """A structured finding extracted from a medical image."""
    finding: str
    location: str = "Unspecified"
    confidence: UncertaintyLevel = UncertaintyLevel.MODERATE
    source: str = "medical_vision_service"
    severity: str = "unknown"  # normal, mild, moderate, severe
    details: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["confidence"] = self.confidence.value
        d["uncertainty"] = self.confidence.value
        return d


@dataclass
class VisionAnalysisResult:
    """The aggregate analysis of an uploaded medical image."""
    image_path: str
    image_modality: str = "Chest X-Ray"
    findings: list[VisionFinding] = field(default_factory=list)
    overall_impression: str = ""
    technical_quality: str = "adequate"
    model_used: str = ""
    disclaimer: str = (
        "Model finding only. Requires clinician and radiologist verification. "
        "Not a definitive radiological diagnosis."
    )
    raw_response: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "image_path": self.image_path,
            "image_modality": self.image_modality,
            "findings": [f.to_dict() for f in self.findings],
            "overall_impression": self.overall_impression,
            "technical_quality": self.technical_quality,
            "model_used": self.model_used,
            "disclaimer": self.disclaimer,
            "raw_response": self.raw_response,
        }


class BaseMedicalVisionAdapter(ABC):
    """Abstract interface for medical vision backends."""

    @abstractmethod
    def analyze_image(
        self,
        image_path: Path,
        clinical_context: str = "",
    ) -> VisionAnalysisResult:
        """Analyze an image and return structured findings."""
        ...
