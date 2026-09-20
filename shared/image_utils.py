from __future__ import annotations

from typing import Any

import cv2
import numpy as np
from PySide6.QtCore import Qt

try:
    from PySide6.QtCore import QSize
    from PySide6.QtGui import QImage, QPixmap
except ImportError:  # pragma: no cover - GUI-only fallback
    QSize = Any  # type: ignore[assignment]
    QImage = Any  # type: ignore[assignment]
    QPixmap = Any  # type: ignore[assignment]


def bgr_to_rgb(image: np.ndarray) -> np.ndarray:
    if image.ndim == 2:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def rgb_to_bgr(image: np.ndarray) -> np.ndarray:
    if image.ndim == 2:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)


def grayscale_to_rgb(image: np.ndarray) -> np.ndarray:
    if image.ndim == 3:
        return image
    return cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)


def normalize_for_display(image: np.ndarray) -> np.ndarray:
    if image.dtype == np.uint8:
        return image
    normalized = cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX)
    return normalized.astype(np.uint8)


def resize_for_display(image: np.ndarray, max_width: int, max_height: int) -> np.ndarray:
    height, width = image.shape[:2]
    if width == 0 or height == 0:
        return image

    scale = min(max_width / width, max_height / height)
    if scale >= 1.0:
        return image.copy()

    new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
    return cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)


def image_dimensions(image: np.ndarray) -> tuple[int, int]:
    height, width = image.shape[:2]
    return width, height


def numpy_to_qimage(image: np.ndarray) -> QImage:
    rgb = normalize_for_display(grayscale_to_rgb(bgr_to_rgb(image) if image.ndim == 3 else image))
    height, width, channels = rgb.shape
    bytes_per_line = channels * width
    return QImage(rgb.data, width, height, bytes_per_line, QImage.Format.Format_RGB888).copy()


def numpy_to_qpixmap(image: np.ndarray) -> QPixmap:
    return QPixmap.fromImage(numpy_to_qimage(image))


def scale_pixmap_for_viewport(
    pixmap: QPixmap,
    viewport_size: QSize,
    device_pixel_ratio: float,
    transformation: Qt.TransformationMode = Qt.TransformationMode.SmoothTransformation,
) -> QPixmap:
    """Scale a preview at the screen's physical resolution.

    Qt widget sizes are expressed in logical pixels. Rendering a pixmap at only
    that logical size makes it look soft on 125%/150% Windows displays because
    Qt must enlarge it again for the physical screen pixels.
    """
    if viewport_size.width() <= 0 or viewport_size.height() <= 0:
        return pixmap

    ratio = max(1.0, device_pixel_ratio)
    physical_size = QSize(
        max(1, round(viewport_size.width() * ratio)),
        max(1, round(viewport_size.height() * ratio)),
    )
    scaled = pixmap.scaled(
        physical_size,
        Qt.AspectRatioMode.KeepAspectRatio,
        transformation,
    )
    scaled.setDevicePixelRatio(ratio)
    return scaled
