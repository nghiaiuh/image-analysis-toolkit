from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from PySide6.QtCore import QPoint, QPointF, QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QWheelEvent
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from shared.image_utils import numpy_to_qpixmap, scale_pixmap_for_viewport


@dataclass
class CanvasGeometry:
    target_rect: QRect
    image_width: int
    image_height: int


class _CanvasArea(QWidget):
    cropRectChanged = Signal(tuple)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("canvasViewport")
        self._image: np.ndarray | None = None
        self._pixmap = None
        self._crop_enabled = False
        self._crop_rect: tuple[int, int, int, int] | None = None
        self._drag_start: QPoint | None = None
        self._drag_current: QPoint | None = None
        self._view_scale = 1.0
        self._view_offset = QPointF()
        self.setMinimumSize(260, 220)
        self.setMouseTracking(True)

    @property
    def image(self) -> np.ndarray | None:
        return self._image

    def set_image(self, image: np.ndarray | None) -> None:
        self._image = image
        self._pixmap = numpy_to_qpixmap(image) if image is not None else None
        self._view_scale = 1.0
        self._view_offset = QPointF()
        self.update()

    def set_crop_enabled(self, enabled: bool) -> None:
        self._crop_enabled = enabled
        if not enabled:
            self._drag_start = None
            self._drag_current = None
        self.update()

    def set_crop_rect(self, rect: tuple[int, int, int, int] | None) -> None:
        self._crop_rect = rect
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.fillRect(self.rect(), QColor("#0d0f14"))

        if self._pixmap is None:
            painter.setPen(QColor("#7a8499"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No image loaded")
            return

        geometry = self._display_geometry()
        scaled, target = self._rendered_pixmap_and_rect(geometry)
        painter.drawPixmap(target, scaled)

        if self._crop_rect:
            self._draw_image_rect(painter, self._crop_rect, target, geometry.image_width, geometry.image_height)
        elif self._drag_start and self._drag_current:
            drag_rect = QRect(self._drag_start, self._drag_current).normalized()
            painter.setPen(QPen(QColor("#5b8cff"), 2, Qt.PenStyle.DashLine))
            painter.drawRect(drag_rect)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if not self._crop_enabled or self._image is None or event.button() != Qt.MouseButton.LeftButton:
            return
        self._drag_start = event.position().toPoint()
        self._drag_current = self._drag_start
        self.update()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._drag_start is None or not self._crop_enabled:
            return
        self._drag_current = event.position().toPoint()
        self.update()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if self._drag_start is None or self._image is None or not self._crop_enabled:
            return

        self._drag_current = event.position().toPoint()
        crop_rect = self._widget_rect_to_image_rect(QRect(self._drag_start, self._drag_current).normalized())
        self._drag_start = None
        self._drag_current = None

        if crop_rect:
            self._crop_rect = crop_rect
            self.cropRectChanged.emit(crop_rect)
        self.update()

    def wheelEvent(self, event: QWheelEvent) -> None:  # noqa: N802
        if self._pixmap is None or not event.angleDelta().y():
            event.ignore()
            return

        geometry = self._display_geometry()
        _, old_target = self._rendered_pixmap_and_rect(geometry)
        factor = 1.25 if event.angleDelta().y() > 0 else 0.8
        new_scale = max(0.25, min(16.0, self._view_scale * factor))
        if new_scale == self._view_scale:
            event.accept()
            return

        cursor = event.position()
        relative_x = max(0.0, min(1.0, (cursor.x() - old_target.x()) / max(1, old_target.width())))
        relative_y = max(0.0, min(1.0, (cursor.y() - old_target.y()) / max(1, old_target.height())))
        self._view_scale = new_scale
        _, new_target = self._rendered_pixmap_and_rect(geometry)
        center_x = cursor.x() - relative_x * new_target.width() + new_target.width() / 2
        center_y = cursor.y() - relative_y * new_target.height() + new_target.height() / 2
        self._view_offset = QPointF(center_x - self.rect().center().x(), center_y - self.rect().center().y())
        self.update()
        event.accept()

    def _display_geometry(self) -> CanvasGeometry:
        if self._image is None:
            return CanvasGeometry(self.rect().adjusted(12, 12, -12, -12), 1, 1)
        height, width = self._image.shape[:2]
        return CanvasGeometry(self.rect().adjusted(12, 12, -12, -12), width, height)

    def _widget_rect_to_image_rect(self, widget_rect: QRect) -> tuple[int, int, int, int] | None:
        if self._image is None:
            return None

        geometry = self._display_geometry()
        image_width = geometry.image_width
        image_height = geometry.image_height
        _, draw_rect = self._rendered_pixmap_and_rect(geometry)
        scale = min(draw_rect.width() / image_width, draw_rect.height() / image_height)

        clipped = widget_rect.intersected(draw_rect)
        if clipped.width() < 2 or clipped.height() < 2:
            return None

        x = int((clipped.x() - draw_rect.x()) / scale)
        y = int((clipped.y() - draw_rect.y()) / scale)
        width = int(clipped.width() / scale)
        height = int(clipped.height() / scale)

        x = max(0, min(image_width - 1, x))
        y = max(0, min(image_height - 1, y))
        width = max(1, min(image_width - x, width))
        height = max(1, min(image_height - y, height))
        return (x, y, width, height)

    def _rendered_pixmap_and_rect(self, geometry: CanvasGeometry):
        viewport_size = QSize(
            max(1, round(geometry.target_rect.width() * self._view_scale)),
            max(1, round(geometry.target_rect.height() * self._view_scale)),
        )
        transformation = (
            Qt.TransformationMode.FastTransformation
            if self._view_scale > 1.0
            else Qt.TransformationMode.SmoothTransformation
        )
        scaled = scale_pixmap_for_viewport(
            self._pixmap,
            viewport_size,
            self.devicePixelRatioF(),
            transformation,
        )
        target = QRect(geometry.target_rect)
        target.setSize(scaled.deviceIndependentSize().toSize())
        target.moveCenter(self.rect().center() + self._view_offset.toPoint())
        return scaled, target

    def _draw_image_rect(
        self,
        painter: QPainter,
        rect: tuple[int, int, int, int],
        draw_rect: QRect,
        image_width: int,
        image_height: int,
    ) -> None:
        x, y, width, height = rect
        scale = min(draw_rect.width() / image_width, draw_rect.height() / image_height)
        mapped = QRect(
            draw_rect.x() + int(x * scale),
            draw_rect.y() + int(y * scale),
            int(width * scale),
            int(height * scale),
        )
        painter.setPen(QPen(QColor("#5b8cff"), 2, Qt.PenStyle.SolidLine))
        painter.drawRect(mapped)
        painter.fillRect(mapped, QColor(91, 140, 255, 30))


class ImageCanvas(QWidget):
    cropRectChanged = Signal(tuple)

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("panelTitle")
        self.canvas = _CanvasArea()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(self.title_label)
        layout.addWidget(self.canvas, 1)

        self.canvas.cropRectChanged.connect(self.cropRectChanged.emit)

    @property
    def image(self) -> np.ndarray | None:
        return self.canvas.image

    def set_image(self, image: np.ndarray | None) -> None:
        self.canvas.set_image(image)

    def set_title(self, title: str) -> None:
        self.title_label.setText(title)

    def set_crop_enabled(self, enabled: bool) -> None:
        self.canvas.set_crop_enabled(enabled)

    def set_crop_rect(self, rect: tuple[int, int, int, int] | None) -> None:
        self.canvas.set_crop_rect(rect)
