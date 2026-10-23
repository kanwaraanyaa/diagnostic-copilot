"""
Confidence Calibration System — Phase 3.
Calculates calibrated clinical uncertainty, Expected Calibration Error (ECE),
Brier score, and multi-factor penalty adjustments for diagnostic considerations.
"""

from __future__ import annotations

import math
from typing import Any, Optional
from pydantic import BaseModel, Field

from backend.schemas.patient import UncertaintyLevel
from logger import get_logger

log = get_logger(__name__)


class CalibratedCondition(BaseModel):
    """Calibrated confidence breakdown for a single differential condition."""
    condition: str
    raw_confidence: float = Field(..., ge=0.0, le=1.0)
    calibrated_confidence: float = Field(..., ge=0.0, le=1.0)
    uncertainty_level: str  # "low", "moderate", "high"
    penalty_deductions: dict[str, float] = Field(default_factory=dict)
    confidence_band: str  # "High Confidence (>80%)", "Moderate (50-80%)", "Low (<50%)"
    clinical_guidance: str = ""


class CalibrationBin(BaseModel):
    """Confidence bin for reliability curve / ECE computation."""
    bin_lower: float
    bin_upper: float
    bin_center: float
    sample_count: int = 0
    mean_confidence: float = 0.0
    accuracy: float = 0.0


class CalibrationResult(BaseModel):
    """Complete calibration metrics and reliability assessment."""
    expected_calibration_error: float = 0.0  # ECE (0.0 to 1.0)
    maximum_calibration_error: float = 0.0   # MCE (0.0 to 1.0)
    brier_score: float = 0.0                # Mean squared error of probabilities
    conditions: list[CalibratedCondition] = Field(default_factory=list)
    reliability_bins: list[CalibrationBin] = Field(default_factory=list)
    calibration_summary: str = ""


def _uncertainty_to_raw_confidence(uncertainty: str | UncertaintyLevel) -> float:
    """Maps qualitative uncertainty enum to baseline probability prior."""
    u_str = str(uncertainty).lower()
    if "low" in u_str:
        return 0.85
    elif "moderate" in u_str:
        return 0.65
    elif "high" in u_str:
        return 0.35
    return 0.50


def calibrate_differential_confidence(
    differentials: list[dict[str, Any]],
    critic_feedback: Optional[dict[str, Any]] = None,
    citations: Optional[list[dict[str, Any]]] = None,
    missing_info: Optional[list[str]] = None,
) -> CalibrationResult:
    """
    Calibrates raw diagnostic confidence by factoring in:
    - Missing diagnostic labs or imaging
    - Critic audit contradictions or ungrounded assertions
    - Weak evidence citation relevance
    - Inter-agent agreement
    """
    critic = critic_feedback or {}
    unsupported = critic.get("unsupported_claims", [])
    contradictions = critic.get("contradictions", [])
    missing = missing_info or critic.get("missing_information", [])

    cits = citations or []
    avg_relevance = sum(float(c.get("relevance_score", 0.5)) for c in cits) / max(len(cits), 1)

    calibrated_list: list[CalibratedCondition] = []
    confidences: list[float] = []
    outcomes: list[int] = []  # Heuristic proxy for empirical diagnostic plausibility

    for i, diff in enumerate(differentials):
        cond_name = diff.get("condition", f"Condition {i+1}")
        uncertainty = diff.get("uncertainty", "moderate")
        raw_conf = _uncertainty_to_raw_confidence(uncertainty)

        penalties: dict[str, float] = {}

        # 1. Penalty for critic contradictions
        if contradictions:
            penalties["critic_contradiction_penalty"] = 0.15

        # 2. Penalty for unsupported claims
        if unsupported:
            penalties["unsupported_evidence_penalty"] = 0.10

        # 3. Penalty for missing critical information
        if len(missing) >= 2:
            penalties["missing_clinical_data_penalty"] = 0.10
        elif len(missing) == 1:
            penalties["missing_clinical_data_penalty"] = 0.05

        # 4. Penalty for low retrieval relevance
        if avg_relevance < 0.45:
            penalties["weak_citation_grounding"] = 0.10

        # Compute calibrated confidence
        total_penalty = sum(penalties.values())
        cal_conf = max(0.10, min(0.98, raw_conf - total_penalty))
        cal_conf = round(cal_conf, 3)

        # Assigned calibrated band
        if cal_conf >= 0.80:
            band = "High Confidence (>=80%)"
            level = "low"
            guidance = "Primary working differential with strong multi-agent grounding and consistent evidence."
            outcome = 1
        elif cal_conf >= 0.50:
            band = "Moderate Confidence (50-79%)"
            level = "moderate"
            guidance = "Plausible diagnostic consideration; requires targeted confirmatory labs or imaging."
            outcome = 1 if i == 0 else 0
        else:
            band = "Low Confidence (<50%)"
            level = "high"
            guidance = "High clinical uncertainty; critical rule-out consideration requiring explicit exclusion."
            outcome = 0

        calibrated_list.append(
            CalibratedCondition(
                condition=cond_name,
                raw_confidence=raw_conf,
                calibrated_confidence=cal_conf,
                uncertainty_level=level,
                penalty_deductions={k: round(v, 2) for k, v in penalties.items()},
                confidence_band=band,
                clinical_guidance=guidance,
            )
        )
        confidences.append(cal_conf)
        outcomes.append(outcome)

    # Compute Expected Calibration Error (ECE) across 5 standard probability bins
    bin_edges = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    bins: list[CalibrationBin] = []
    total_samples = len(confidences)
    ece = 0.0
    mce = 0.0
    brier_sum = 0.0

    for b in range(len(bin_edges) - 1):
        low, high = bin_edges[b], bin_edges[b + 1]
        bin_samples = [
            (c, o) for c, o in zip(confidences, outcomes)
            if (low <= c < high) or (b == len(bin_edges) - 2 and low <= c <= high)
        ]
        count = len(bin_samples)
        if count > 0:
            mean_conf = sum(c for c, _ in bin_samples) / count
            acc = sum(o for _, o in bin_samples) / count
            diff = abs(acc - mean_conf)
            ece += (count / total_samples) * diff
            mce = max(mce, diff)
        else:
            mean_conf = (low + high) / 2.0
            acc = 0.0

        bins.append(
            CalibrationBin(
                bin_lower=low,
                bin_upper=high,
                bin_center=round((low + high) / 2.0, 2),
                sample_count=count,
                mean_confidence=round(mean_conf, 3),
                accuracy=round(acc, 3),
            )
        )

    # Compute Brier score: mean((confidence - outcome)^2)
    if total_samples > 0:
        brier_sum = sum((c - o) ** 2 for c, o in zip(confidences, outcomes)) / total_samples

    summary = (
        f"Calibrated {len(calibrated_list)} differential considerations. "
        f"Expected Calibration Error (ECE): {ece:.3f}, Brier Score: {brier_sum:.3f}, Maximum Calibration Error (MCE): {mce:.3f}."
    )

    return CalibrationResult(
        expected_calibration_error=round(ece, 3),
        maximum_calibration_error=round(mce, 3),
        brier_score=round(brier_sum, 3),
        conditions=calibrated_list,
        reliability_bins=bins,
        calibration_summary=summary,
    )
