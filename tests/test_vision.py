"""
Tests for Medical Vision Service and image preprocessing — Phase 2.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from vision.base import VisionAnalysisResult, VisionFinding
from vision.medical_vision import LocalDemoVisionAdapter, MedicalVisionService
from vision.preprocessing import (
    ImagePreprocessingError,
    preprocess_image,
    validate_image_path,
)


@pytest.fixture
def sample_cxr_image(tmp_path: Path) -> Path:
    """Generate a synthetic chest X-ray image for testing."""
    img_path = tmp_path / "synthetic_cxr.png"
    img = Image.new("L", (512, 512), color=40)
    # Draw simple gradient/blocks to simulate hemithorax
    for x in range(100, 220):
        for y in range(150, 400):
            img.putpixel((x, y), 120)  # Left lung
    for x in range(292, 412):
        for y in range(150, 400):
            img.putpixel((x, y), 90)   # Right lung (mild opacity)
    img.save(img_path)
    return img_path


class TestImagePreprocessing:
    """Tests for image validation and preprocessing."""

    def test_valid_image_path(self, sample_cxr_image: Path):
        validated = validate_image_path(sample_cxr_image)
        assert validated == sample_cxr_image

    def test_nonexistent_image_raises(self, tmp_path: Path):
        with pytest.raises(ImagePreprocessingError, match="not found"):
            validate_image_path(tmp_path / "does_not_exist.png")

    def test_unsupported_extension_raises(self, tmp_path: Path):
        bad_file = tmp_path / "test.txt"
        bad_file.write_text("not an image")
        with pytest.raises(ImagePreprocessingError, match="Unsupported file format"):
            validate_image_path(bad_file)

    def test_preprocess_image_resizing_and_rgb(self, tmp_path: Path):
        # Create oversized image
        big_path = tmp_path / "large_image.jpg"
        big_img = Image.new("RGB", (2500, 3000), color=(100, 100, 100))
        big_img.save(big_path)

        out_path, meta = preprocess_image(big_path, output_dir=tmp_path, target_max_size=1024)
        assert out_path.exists()
        assert meta["resized"] is True
        assert max(meta["processed_dimensions"]) <= 1024
        assert meta["color_mode"] == "RGB"


class TestMedicalVisionService:
    """Tests for MedicalVisionService and local adapter."""

    def test_local_adapter_findings(self, sample_cxr_image: Path):
        adapter = LocalDemoVisionAdapter()
        result = adapter.analyze_image(
            sample_cxr_image,
            clinical_context="Patient has productive cough and fever",
        )
        assert isinstance(result, VisionAnalysisResult)
        assert len(result.findings) > 0
        assert any("opacity" in f.finding.lower() or "consolidation" in f.finding.lower() for f in result.findings)
        assert result.technical_quality == "adequate"

    def test_vision_service_facade(self, sample_cxr_image: Path):
        service = MedicalVisionService(adapter=LocalDemoVisionAdapter())
        result = service.analyze(sample_cxr_image, clinical_context="shortness of breath")
        assert len(result.findings) > 0
        assert result.image_modality == "Chest Radiograph (CXR)"
