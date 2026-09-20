from __future__ import annotations

from dataclasses import dataclass
import math
import time

import cv2
import numpy as np

from apps.image_viewer.processing.zoom import INTERPOLATION_MAP
from shared.image_utils import image_dimensions
from shared.validators import validate_image_array

BORDER_MODE_MAP = {
    "Constant Black": cv2.BORDER_CONSTANT,
    "Replicate": cv2.BORDER_REPLICATE,
    "Reflect": cv2.BORDER_REFLECT,
}


@dataclass(slots=True)
class RotationResult:
    image: np.ndarray
    angle: float
    interpolation: str
    border_mode: str
    matrix: np.ndarray
    original_size: tuple[int, int]
    output_size: tuple[int, int]
    clipping_occurs: bool
    processing_time_ms: float


def _rotation_clips(width: int, height: int, angle: float) -> bool:
    radians = math.radians(abs(angle))
    bbox_width = abs(width * math.cos(radians)) + abs(height * math.sin(radians))
    bbox_height = abs(width * math.sin(radians)) + abs(height * math.cos(radians))
    return bbox_width > width + 1 or bbox_height > height + 1


def apply_rotate(
    image: np.ndarray,
    angle: float,
    center: tuple[float, float] | None = None,
    border_mode: str = "Constant Black",
    interpolation: str = "Bilinear",
) -> RotationResult:
    validate_image_array(image)
    if interpolation not in INTERPOLATION_MAP:
        raise ValueError(f"Unsupported interpolation: {interpolation}")
    if border_mode not in BORDER_MODE_MAP:
        raise ValueError(f"Unsupported border mode: {border_mode}")

    height, width = image.shape[:2]
    rotation_center = center if center is not None else (width / 2.0, height / 2.0)
    matrix = cv2.getRotationMatrix2D(rotation_center, angle, 1.0)

    start = time.perf_counter()
    rotated = cv2.warpAffine(
        image,
        matrix,
        (width, height),
        flags=INTERPOLATION_MAP[interpolation],
        borderMode=BORDER_MODE_MAP[border_mode],
        borderValue=(0, 0, 0),
    )
    elapsed = (time.perf_counter() - start) * 1000

    return RotationResult(
        image=rotated,
        angle=angle,
        interpolation=interpolation,
        border_mode=border_mode,
        matrix=matrix,
        original_size=image_dimensions(image),
        output_size=image_dimensions(rotated),
        clipping_occurs=_rotation_clips(width, height, angle),
        processing_time_ms=elapsed,
    )


def apply_rotation(
    image: np.ndarray,
    angle: float,
    interpolation: str = "Bilinear",
    border_mode: str = "Constant Black",
    center: tuple[float, float] | None = None,
) -> RotationResult:
    """Rotate around the image center by default, with optional custom-center support."""
    return apply_rotate(
        image=image,
        angle=angle,
        center=center,
        border_mode=border_mode,
        interpolation=interpolation,
    )
