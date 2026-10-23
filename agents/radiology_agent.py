"""
Radiology Agent — Phase 2.

Responsibilities:
- Evaluates uploaded radiographic studies (e.g. Chest X-Ray)
- Coordinates with MedicalVisionService
- Extracts structured visual findings with calibrated uncertainty
- Distinguishes objective radiological patterns from presumptive clinical diagnoses
"""

from __future__ import annotations

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pathlib import Path
from typing import Any

from graph.state import DiagnosticState
from logger import get_logger
from vision.medical_vision import MedicalVisionService

log = get_logger(__name__)


def radiology_agent_node(state: DiagnosticState) -> dict[str, Any]:
    """LangGraph node for Radiology Agent."""
    log.info("radiology_agent_started")
    logs = list(state.get("agent_logs", []))

    image_path_str = state.get("image_path")
    gp_summary = state.get("gp_assessment", {}).get("patient_summary", "")

    if not image_path_str or not Path(image_path_str).exists():
        assessment = {
            "status": "no_image_provided",
            "findings": [],
            "overall_impression": "No radiographic image provided for this patient encounter.",
            "technical_quality": "N/A",
            "clinical_correlation": "Imaging assessment deferred pending acquisition of relevant radiographs.",
        }
        logs.append({
            "agent": "Radiology Agent",
            "action": "Assessment completed: No imaging study submitted",
            "findings_count": 0,
        })
        return {
            "image_findings": [],
            "radiology_assessment": assessment,
            "agent_logs": logs,
        }

    # If previously analyzed in debate cycle, reuse assessment without recomputing
    if state.get("radiology_assessment") and state.get("iteration_count", 0) > 0:
        log.info("radiology_agent_reusing_assessment")
        return {
            "image_findings": state.get("image_findings", []),
            "radiology_assessment": state.get("radiology_assessment", {}),
            "agent_logs": logs,
        }

    try:
        vision_service = MedicalVisionService()
        result = vision_service.analyze(
            image_path=image_path_str,
            clinical_context=gp_summary,
        )

        findings_dict_list = [f.to_dict() for f in result.findings]
        is_unavailable = result.model_used == "unavailable" or "unavailable" in result.overall_impression.lower()
        status = "unavailable" if is_unavailable else "analyzed"
        limitations = (
            ["Image analysis unavailable or unconfigured. Manual radiological read required."]
            if is_unavailable
            else [
                "Preliminary automated visual pattern screening.",
                "Findings require clinical correlation and radiologist verification.",
            ]
        )

        assessment = {
            "status": status,
            "image_modality": result.image_modality,
            "technical_quality": result.technical_quality,
            "model_used": result.model_used,
            "overall_impression": result.overall_impression,
            "findings": findings_dict_list,
            "limitations": limitations,
            "disclaimer": result.disclaimer,
        }

        logs.append({
            "agent": "Radiology Agent",
            "action": f"Evaluated {result.image_modality} (Status: {status}); findings: {len(findings_dict_list)}",
            "findings_count": len(findings_dict_list),
            "status": status,
        })

        return {
            "image_findings": findings_dict_list,
            "radiology_assessment": assessment,
            "agent_logs": logs,
        }

    except Exception as e:
        log.error("radiology_agent_error", error=str(e))
        assessment = {
            "status": "unavailable",
            "findings": [],
            "overall_impression": f"Image analysis unavailable: {e}",
            "limitations": [f"Processing exception: {e}"],
            "technical_quality": "suboptimal",
        }
        logs.append({
            "agent": "Radiology Agent",
            "action": f"Image processing error: {e}",
            "findings_count": 0,
            "status": "error",
        })
        return {
            "image_findings": [],
            "radiology_assessment": assessment,
            "agent_logs": logs,
        }
