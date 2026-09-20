from __future__ import annotations

from dataclasses import dataclass
import time

import cv2
import numpy as np

from shared.image_utils import image_dimensions
from shared.validators import validate_image_array

INTERPOLATION_MAP = {
    "Nearest Neighbor": cv2.INTER_NEAREST,
    "Bilinear": cv2.INTER_LINEAR,
    "Bicubic": cv2.INTER_CUBIC,
}


@dataclass(slots=True)
class ZoomResult:
    image: np.ndarray
    scale: float
    interpolation: str
    original_size: tuple[int, int]
    output_size: tuple[int, int]
    processing_time_ms: float


def apply_zoom(image: np.ndarray, scale: float, interpolation: str) -> ZoomResult:
    validate_image_array(image)
    if scale <= 0:
        raise ValueError("Zoom scale must be positive.")
    if interpolation not in INTERPOLATION_MAP:
        raise ValueError(f"Unsupported interpolation: {interpolation}")

    original_size = image_dimensions(image)
    start = time.perf_counter()
    H, W = image.shape[:2]
    W_new = max(1, round(W * scale))
    H_new = max(1, round(H * scale))
    zoomed = cv2.resize(image, (W_new, H_new), interpolation=INTERPOLATION_MAP[interpolation])
    elapsed = (time.perf_counter() - start) * 1000

    return ZoomResult(
        image=zoomed,
        scale=scale,
        interpolation=interpolation,
        original_size=original_size,
        output_size=image_dimensions(zoomed),
        processing_time_ms=elapsed,
    )

