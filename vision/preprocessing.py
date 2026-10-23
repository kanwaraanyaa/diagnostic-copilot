"""
Image validation and preprocessing pipeline for medical images — Phase 2.
"""

from __future__ import annotations

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pathlib import Path
from typing import Tuple
from PIL import Image, ImageEnhance, ImageOps

from logger import get_logger

log = get_logger(__name__)

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".dcm"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_IMAGE_DIMENSION = 2048
MIN_IMAGE_DIMENSION = 64


class ImagePreprocessingError(Exception):
    """Raised when image validation or preprocessing fails."""
    pass


def validate_image_path(path: Path) -> Path:
    """Validate that the image exists, has supported extension, and acceptable size."""
    if not path.exists():
        raise ImagePreprocessingError(f"Image file not found: {path}")

    ext = path.suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ImagePreprocessingError(
            f"Unsupported file format '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    size = path.stat().st_size
    if size > MAX_FILE_SIZE_BYTES:
        raise ImagePreprocessingError(
            f"File size ({size / (1024 * 1024):.2f}MB) exceeds limit of {MAX_FILE_SIZE_BYTES / (1024 * 1024):.0f}MB."
        )

    return path


def preprocess_image(
    image_path: Path,
    output_dir: Path | None = None,
    target_max_size: int = MAX_IMAGE_DIMENSION,
) -> Tuple[Path, dict]:
    """
    Validate, sanitize, resize, and normalize a medical image for model ingestion.

    Returns:
        (preprocessed_image_path, metadata_dict)
    """
    validated_path = validate_image_path(image_path)

    try:
        with Image.open(validated_path) as img:
            # Auto-orient based on EXIF tag if present
            img = ImageOps.exif_transpose(img)

            orig_w, orig_h = img.size
            if orig_w < MIN_IMAGE_DIMENSION or orig_h < MIN_IMAGE_DIMENSION:
                raise ImagePreprocessingError(
                    f"Image resolution too low ({orig_w}x{orig_h}). Minimum is {MIN_IMAGE_DIMENSION}x{MIN_IMAGE_DIMENSION}."
                )

            # Convert to RGB (handles RGBA, grayscale L, palette P)
            if img.mode != "RGB":
                img = img.convert("RGB")

            # Scale down proportionally if larger than target_max_size
            if max(orig_w, orig_h) > target_max_size:
                ratio = target_max_size / float(max(orig_w, orig_h))
                new_w = int(orig_w * ratio)
                new_h = int(orig_h * ratio)
                img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                resized = True
            else:
                new_w, new_h = orig_w, orig_h
                resized = False

            # Mild contrast enhancement suitable for clinical radiographs
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.05)

            # Determine output destination
            if output_dir is None:
                output_dir = validated_path.parent
            output_dir.mkdir(parents=True, exist_ok=True)

            out_filename = f"preprocessed_{validated_path.stem}.png"
            out_path = output_dir / out_filename
            img.save(out_path, format="PNG", optimize=True)

            metadata = {
                "original_filename": validated_path.name,
                "original_dimensions": (orig_w, orig_h),
                "processed_dimensions": (new_w, new_h),
                "resized": resized,
                "format": "PNG",
                "color_mode": "RGB",
            }
            log.info("image_preprocessed", input=str(validated_path), output=str(out_path), metadata=metadata)
            return out_path, metadata

    except ImagePreprocessingError:
        raise
    except Exception as e:
        log.error("image_processing_failed", path=str(validated_path), error=str(e))
        raise ImagePreprocessingError(f"Failed to process image: {e}") from e
