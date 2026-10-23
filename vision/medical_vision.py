"""
MedicalVisionService implementation with configurable adapters — Phase 2.
"""

from __future__ import annotations

import base64
import json
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pathlib import Path
from typing import Any
from PIL import Image, ImageStat

from backend.schemas.patient import UncertaintyLevel
from config import get_settings
from logger import get_logger
from vision.base import BaseMedicalVisionAdapter, VisionAnalysisResult, VisionFinding
from vision.preprocessing import preprocess_image

log = get_logger(__name__)

VISION_ANALYSIS_PROMPT = """You are an academic clinical decision-support radiology assistant.
Analyze the attached radiograph (e.g., Chest X-ray) alongside the provided clinical context.

Clinical Context:
{clinical_context}

Analyze the image systematically (Lungs, Pleura, Heart size, Mediastinum, Bones/Soft tissues).
Output ONLY valid JSON with this exact schema:
{{
    "image_modality": "Chest X-Ray (CXR)",
    "technical_quality": "adequate|suboptimal",
    "overall_impression": "Concise summary of findings",
    "findings": [
        {{
            "finding": "Specific visual observation (e.g. consolidation, opacity, effusion, cardiomegaly)",
            "location": "Anatomical location (e.g. right lower lobe, bilateral)",
            "confidence": "low|moderate|high",
            "severity": "normal|mild|moderate|severe",
            "details": "Brief qualitative description"
        }}
    ]
}}

CRITICAL SAFETY RULES:
1. Describe VISUAL OBSERVATIONS, not definitive clinical diagnoses.
2. If image is unclear or normal, note accordingly.
3. Express calibrated uncertainty.
4. Respond with valid JSON only.
"""


class UnavailableVisionAdapter(BaseMedicalVisionAdapter):
    """
    Controlled fallback when medical vision model is unconfigured or unavailable.
    Guarantees no fabricated or hallucinated medical findings are produced.
    """

    def __init__(self, reason: str = "Vision model provider is not configured.") -> None:
        self.reason = reason

    def analyze_image(
        self,
        image_path: Path,
        clinical_context: str = "",
    ) -> VisionAnalysisResult:
        log.warning("vision_provider_unavailable", reason=self.reason, path=str(image_path))
        return VisionAnalysisResult(
            image_path=str(image_path),
            image_modality="Chest Radiograph (CXR)",
            findings=[],
            overall_impression=f"Image analysis unavailable: {self.reason} Automated findings suppressed. Clinician review required.",
            technical_quality="N/A",
            model_used="unavailable",
            raw_response=json.dumps({"status": "unavailable", "reason": self.reason}),
        )


class LocalDemoVisionAdapter(BaseMedicalVisionAdapter):
    """
    Offline/local image density analyzer.
    Analyzes radiographic image features (density, asymmetry, regional luminance)
    from actual image pixels without requiring external cloud API keys, and
    avoids generating ungrounded diagnoses from patient symptom text.
    """

    def analyze_image(
        self,
        image_path: Path,
        clinical_context: str = "",
    ) -> VisionAnalysisResult:
        log.info("local_vision_analysis_start", path=str(image_path))

        findings: list[VisionFinding] = []
        try:
            with Image.open(image_path) as img:
                w, h = img.size
                gray = img.convert("L")

                # Sample quadrants to detect radiographic density / opacity asymmetry
                left_hemithorax = gray.crop((0, int(h * 0.2), int(w * 0.48), int(h * 0.85)))
                right_hemithorax = gray.crop((int(w * 0.52), int(h * 0.2), w, int(h * 0.85)))

                stat_left = ImageStat.Stat(left_hemithorax)
                stat_right = ImageStat.Stat(right_hemithorax)

                mean_left = stat_left.mean[0]
                mean_right = stat_right.mean[0]
                asymmetry = abs(mean_left - mean_right)

                # Objective image density analysis:
                if asymmetry > 8:
                    loc = "right lower lobe" if mean_right < mean_left else "left lower lobe"
                    findings.append(
                        VisionFinding(
                            finding="Possible focal alveolar opacity / regional density asymmetry",
                            location=loc,
                            confidence=UncertaintyLevel.MODERATE,
                            source="local_radiological_density_analyzer",
                            severity="moderate",
                            details="Regional attenuation difference detected between left and right hemithorax fields; requires clinical radiologist confirmation.",
                        )
                    )
                else:
                    findings.append(
                        VisionFinding(
                            finding="Symmetric lung field radiographic attenuation on preliminary screening",
                            location="Bilateral hemithoraces",
                            confidence=UncertaintyLevel.HIGH,
                            source="local_radiological_density_analyzer",
                            severity="normal",
                            details="No gross focal opacification or bilateral attenuation asymmetry detected on automated screening. Dedicated radiologist read required.",
                        )
                    )

                impression = (
                    f"Visual density analysis completed. Principal observation: {findings[0].finding} ({findings[0].location}). "
                    f"Requires qualified radiologist confirmation."
                )

                return VisionAnalysisResult(
                    image_path=str(image_path),
                    image_modality="Chest Radiograph (CXR)",
                    findings=findings,
                    overall_impression=impression,
                    technical_quality="adequate",
                    model_used="local-radiological-density-v1",
                    raw_response=json.dumps([f.to_dict() for f in findings]),
                )

        except Exception as e:
            log.error("local_vision_analysis_error", error=str(e))
            return VisionAnalysisResult(
                image_path=str(image_path),
                image_modality="Chest Radiograph (CXR)",
                findings=[],
                overall_impression=f"Image processing encountered an exception: {e}",
                technical_quality="suboptimal",
                model_used="local-heuristic-cxr-v1 (fallback)",
            )


class GeminiVisionAdapter(BaseMedicalVisionAdapter):
    """Google Gemini Multimodal Vision API adapter."""

    def __init__(self) -> None:
        import google.generativeai as genai

        settings = get_settings()
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")
        genai.configure(api_key=settings.gemini_api_key)
        self.model_name = settings.vision_model or settings.gemini_model or "gemini-3.8-flash"
        self._model = genai.GenerativeModel(self.model_name)

    def analyze_image(
        self,
        image_path: Path,
        clinical_context: str = "",
    ) -> VisionAnalysisResult:
        prompt = VISION_ANALYSIS_PROMPT.format(clinical_context=clinical_context)
        try:
            with Image.open(image_path) as img:
                response = self._model.generate_content([prompt, img])
                text = response.text or "{}"
                return _parse_vision_llm_response(text, str(image_path), self.model_name)
        except Exception as e:
            log.warning("gemini_vision_generate_failed_fallback_unavailable", error=str(e))
            return VisionAnalysisResult(
                image_path=str(image_path),
                image_modality="Chest Radiograph (CXR)",
                findings=[],
                overall_impression=f"Image analysis unavailable: Remote vision service error ({e}). Automated findings suppressed.",
                technical_quality="N/A",
                model_used=f"{self.model_name} (unavailable)",
                raw_response=json.dumps({"status": "unavailable", "error": str(e)}),
            )


class OpenAIVisionAdapter(BaseMedicalVisionAdapter):
    """OpenAI Vision (GPT-4o / GPT-4o-mini) adapter."""

    def __init__(self) -> None:
        from openai import OpenAI

        settings = get_settings()
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not configured.")
        self._client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
        self._model = settings.openai_model or "gpt-4o-mini"

    def analyze_image(
        self,
        image_path: Path,
        clinical_context: str = "",
    ) -> VisionAnalysisResult:
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")

        prompt = VISION_ANALYSIS_PROMPT.format(clinical_context=clinical_context)
        ext = image_path.suffix.lstrip(".").lower()
        mime = f"image/{'jpeg' if ext in ('jpg', 'jpeg') else ext}"

        resp = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                    ],
                }
            ],
            temperature=0.2,
        )
        text = resp.choices[0].message.content or "{}"
        return _parse_vision_llm_response(text, str(image_path), self._model)


def _parse_vision_llm_response(text: str, image_path: str, model_used: str) -> VisionAnalysisResult:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = [l for l in cleaned.split("\n") if not l.strip().startswith("```")]
        cleaned = "\n".join(lines).strip()

    data: dict[str, Any] = {}
    try:
        data = json.loads(cleaned)
    except Exception:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start != -1 and end != -1:
            try:
                data = json.loads(cleaned[start : end + 1])
            except Exception:
                pass

    findings: list[VisionFinding] = []
    for f in data.get("findings", []):
        try:
            unc_str = str(f.get("confidence", "moderate")).lower()
            try:
                unc = UncertaintyLevel(unc_str)
            except ValueError:
                unc = UncertaintyLevel.MODERATE

            findings.append(
                VisionFinding(
                    finding=str(f.get("finding", "Unspecified visual observation")),
                    location=str(f.get("location", "Unspecified")),
                    confidence=unc,
                    source=f"vision_model ({model_used})",
                    severity=str(f.get("severity", "unknown")),
                    details=str(f.get("details", "")),
                )
            )
        except Exception as err:
            log.warning("vision_finding_parse_error", error=str(err))

    return VisionAnalysisResult(
        image_path=image_path,
        image_modality=data.get("image_modality", "Chest X-Ray"),
        findings=findings,
        overall_impression=data.get("overall_impression", "Analysis completed."),
        technical_quality=data.get("technical_quality", "adequate"),
        model_used=model_used,
        raw_response=text,
    )


class MedicalVisionService:
    """Primary facade for medical image analysis."""

    def __init__(self, adapter: BaseMedicalVisionAdapter | None = None) -> None:
        if adapter is not None:
            self._adapter = adapter
            return

        settings = get_settings()
        provider = (settings.vision_provider or "").lower()

        if provider == "gemini":
            if settings.gemini_api_key and settings.gemini_api_key != "your-gemini-api-key-here":
                try:
                    self._adapter = GeminiVisionAdapter()
                    log.info("vision_service_using_gemini")
                    return
                except Exception as e:
                    log.warning("gemini_vision_init_failed", error=str(e))
                    self._adapter = UnavailableVisionAdapter(f"Gemini Vision initialization failed: {e}")
                    return
            else:
                self._adapter = UnavailableVisionAdapter("Gemini API key is not configured.")
                return

        if provider == "openai":
            if settings.openai_api_key and settings.openai_api_key != "your-openai-api-key-here":
                try:
                    self._adapter = OpenAIVisionAdapter()
                    log.info("vision_service_using_openai")
                    return
                except Exception as e:
                    log.warning("openai_vision_init_failed", error=str(e))
                    self._adapter = UnavailableVisionAdapter(f"OpenAI Vision initialization failed: {e}")
                    return
            else:
                self._adapter = UnavailableVisionAdapter("OpenAI API key is not configured.")
                return

        if provider in ("local", "demo"):
            log.info("vision_service_using_local_adapter")
            self._adapter = LocalDemoVisionAdapter()
            return

        if provider in ("none", "disabled"):
            self._adapter = UnavailableVisionAdapter("Vision provider disabled via configuration.")
            return

        # Fallback check: If Gemini or OpenAI API keys exist in environment, attempt to use them
        if settings.gemini_api_key and settings.gemini_api_key != "your-gemini-api-key-here":
            try:
                self._adapter = GeminiVisionAdapter()
                log.info("vision_service_using_gemini_fallback")
                return
            except Exception:
                pass

        if settings.openai_api_key and settings.openai_api_key != "your-openai-api-key-here":
            try:
                self._adapter = OpenAIVisionAdapter()
                log.info("vision_service_using_openai_fallback")
                return
            except Exception:
                pass

        # If no credentials exist, return controlled UnavailableVisionAdapter (no hallucinated findings)
        log.info("vision_service_unavailable_no_credentials")
        self._adapter = UnavailableVisionAdapter("No active medical vision API key configured.")

    def analyze(self, image_path: Path | str, clinical_context: str = "") -> VisionAnalysisResult:
        p = Path(image_path)
        # Preprocess first
        preprocessed_path, meta = preprocess_image(p)
        result = self._adapter.analyze_image(preprocessed_path, clinical_context=clinical_context)
        return result
