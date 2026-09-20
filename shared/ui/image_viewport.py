from __future__ import annotations

import numpy as np
from PySide6.QtCore import QPoint, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsPixmapItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from shared.image_utils import image_dimensions, numpy_to_qpixmap


class _ImageGraphicsView(QGraphicsView):
    cropRectChanged = Signal(tuple)

    def __init__(self, scene: QGraphicsScene, parent: QWidget | None = None) -> None:
        super().__init__(scene, parent)
        self._pixmap_item: QGraphicsPixmapItem | None = None
        self._crop_enabled = False
        self._crop_item: QGraphicsRectItem | None = None
        self._drag_origin: QPoint | None = None
        self._panning = False
        self.setObjectName("graphicsViewport")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setBackgroundBrush(QColor("#080D13"))

    def set_pixmap_item(self, item: QGraphicsPixmapItem | None) -> None:
        self._pixmap_item = item
        self.reset_view()

    def set_crop_enabled(self, enabled: bool) -> None:
        self._crop_enabled = enabled
        self.setCursor(Qt.CursorShape.CrossCursor if enabled else Qt.CursorShape.OpenHandCursor)
        if not enabled:
            self._remove_crop_item()

    def set_crop_rect(self, rect: tuple[int, int, int, int] | None) -> None:
        if rect is None:
            self._remove_crop_item()
            return
        self._set_crop_rect(QRectF(*rect), emit=False)

    def crop_rect(self) -> tuple[int, int, int, int] | None:
        if self._crop_item is None:
            return None
        rect = self._crop_item.rect().toAlignedRect()
        return rect.x(), rect.y(), rect.width(), rect.height()

    def reset_view(self) -> None:
        if self._pixmap_item is None:
            return
        self.resetTransform()
        self.fitInView(self._pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)

    def actual_size(self) -> None:
        self.resetTransform()
        self.centerOn(self.sceneRect().center())

    def wheelEvent(self, event) -> None:  # noqa: N802
        if self._pixmap_item is None:
            return
        factor = 1.18 if event.angleDelta().y() > 0 else 1 / 1.18
        next_scale = self.transform().m11() * factor
        if 0.05 <= next_scale <= 40:
            self.scale(factor, factor)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.MiddleButton or (
            event.button() == Qt.MouseButton.LeftButton and not self._crop_enabled
        ):
            self._panning = True
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            synthetic = event
            super().mousePressEvent(synthetic)
            return
        if event.button() == Qt.MouseButton.LeftButton and self._crop_enabled and self._pixmap_item is not None:
            self._drag_origin = event.position().toPoint()
            self._set_crop_rect(QRectF(self.mapToScene(self._drag_origin), self.mapToScene(self._drag_origin)), emit=False)
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._drag_origin is not None and self._crop_enabled:
            start = self.mapToScene(self._drag_origin)
            end = self.mapToScene(event.position().toPoint())
            self._set_crop_rect(QRectF(start, end).normalized(), emit=False)
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if self._panning:
            self._panning = False
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            super().mouseReleaseEvent(event)
            return
        if self._drag_origin is not None and event.button() == Qt.MouseButton.LeftButton:
            self._drag_origin = None
            rect = self.crop_rect()
            if rect and rect[2] > 1 and rect[3] > 1:
                self.cropRectChanged.emit(rect)
            return
        super().mouseReleaseEvent(event)

    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:  # noqa: N802
        super().drawBackground(painter, rect)
        cell = 18
        first_x = int(rect.left() // cell) * cell
        first_y = int(rect.top() // cell) * cell
        painter.fillRect(rect, QColor("#080D13"))
        shade = QColor(255, 255, 255, 5)
        for x in range(first_x, int(rect.right()) + cell, cell):
            for y in range(first_y, int(rect.bottom()) + cell, cell):
                if ((x // cell) + (y // cell)) % 2:
                    painter.fillRect(QRectF(x, y, cell, cell), shade)

    def drawForeground(self, painter: QPainter, rect: QRectF) -> None:  # noqa: N802
        super().drawForeground(painter, rect)
        if self._crop_item is None or self._pixmap_item is None:
            return
        crop = self._crop_item.rect()
        image_rect = self._pixmap_item.boundingRect()
        outside = QPainterPath()
        outside.addRect(image_rect)
        inside = QPainterPath()
        inside.addRect(crop)
        painter.fillPath(outside.subtracted(inside), QColor(0, 0, 0, 95))
        painter.setPen(QPen(QColor("#22D3EE"), 1.4 / max(self.transform().m11(), 0.01)))
        painter.drawRect(crop)
        size = 7 / max(self.transform().m11(), 0.01)
        painter.setBrush(QColor("#22D3EE"))
        painter.setPen(Qt.PenStyle.NoPen)
        for point in (crop.topLeft(), crop.topRight(), crop.bottomLeft(), crop.bottomRight()):
            painter.drawRoundedRect(QRectF(point.x() - size / 2, point.y() - size / 2, size, size), size / 4, size / 4)

    def _set_crop_rect(self, rect: QRectF, emit: bool) -> None:
        if self._pixmap_item is None:
            return
        bounded = rect.intersected(self._pixmap_item.boundingRect())
        if self._crop_item is None:
            self._crop_item = QGraphicsRectItem()
            self._crop_item.setPen(QPen(Qt.PenStyle.NoPen))
            self._crop_item.setBrush(Qt.BrushStyle.NoBrush)
            self._crop_item.setZValue(10)
            self.scene().addItem(self._crop_item)
        self._crop_item.setRect(bounded)
        self.viewport().update()
        if emit:
            value = self.crop_rect()
            if value:
                self.cropRectChanged.emit(value)

    def _remove_crop_item(self) -> None:
        if self._crop_item is not None:
            self.scene().removeItem(self._crop_item)
            self._crop_item = None
        self.viewport().update()


class ImageViewport(QWidget):
    """Reusable OpenCV/NumPy image viewport with native Qt zoom, pan and crop selection."""

    cropRectChanged = Signal(tuple)

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._image: np.ndarray | None = None
        self._scene = QGraphicsScene(self)
        self._pixmap_item = QGraphicsPixmapItem()
        self._scene.addItem(self._pixmap_item)
        self.view = _ImageGraphicsView(self._scene)
        self.view.cropRectChanged.connect(self.cropRectChanged.emit)
        self.setObjectName("panel")

        self.title_label = QLabel(title)
        self.title_label.setObjectName("panelTitle")
        self.metadata_label = QLabel("Không có ảnh")
        self.metadata_label.setObjectName("canvasMetadata")
        header = QHBoxLayout()
        header.setContentsMargins(12, 10, 12, 0)
        header.addWidget(self.title_label)
        header.addStretch(1)
        header.addWidget(self.metadata_label)

        self.fit_button = QPushButton("Vừa khung")
        self.one_to_one_button = QPushButton("1:1")
        self.reset_button = QPushButton("Đặt lại")
        for button in (self.fit_button, self.one_to_one_button, self.reset_button):
            button.setToolTip("Vừa ảnh với khung" if button is self.fit_button else "Kích thước thật" if button is self.one_to_one_button else "Đặt lại khung xem")
            button.setFixedHeight(27)
        controls = QHBoxLayout()
        controls.setContentsMargins(12, 0, 12, 10)
        controls.addWidget(self.fit_button)
        controls.addWidget(self.one_to_one_button)
        controls.addWidget(self.reset_button)
        controls.addStretch(1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(7)
        layout.addLayout(header)
        layout.addWidget(self.view, 1)
        layout.addLayout(controls)

        self.fit_button.clicked.connect(self.view.reset_view)
        self.reset_button.clicked.connect(self.view.reset_view)
        self.one_to_one_button.clicked.connect(self.view.actual_size)
        self._show_empty_state()

    @property
    def image(self) -> np.ndarray | None:
        return self._image

    def set_title(self, title: str) -> None:
        self.title_label.setText(title)

    def set_image(self, image: np.ndarray | None) -> None:
        self._image = image
        self._scene.clear()
        self._pixmap_item = QGraphicsPixmapItem()
        self._scene.addItem(self._pixmap_item)
        if image is None:
            self._show_empty_state()
            self.view.set_pixmap_item(None)
            return
        pixmap: QPixmap = numpy_to_qpixmap(image)
        self._pixmap_item.setPixmap(pixmap)
        self._scene.setSceneRect(self._pixmap_item.boundingRect())
        width, height = image_dimensions(image)
        channels = 1 if image.ndim == 2 else image.shape[2]
        self.metadata_label.setText(f"{width} × {height}  ·  {channels} kênh")
        self.view.set_pixmap_item(self._pixmap_item)

    def set_crop_enabled(self, enabled: bool) -> None:
        self.view.set_crop_enabled(enabled)

    def set_crop_rect(self, rect: tuple[int, int, int, int] | None) -> None:
        self.view.set_crop_rect(rect)

    def _show_empty_state(self) -> None:
        self.metadata_label.setText("Đang chờ ảnh")
        self._scene.clear()
        message = self._scene.addText("Thả ảnh vào đây\nhoặc dùng Mở ảnh")
        message.setDefaultTextColor(QColor("#8E9CAB"))
        message.setPos(-95, -28)
        self._scene.setSceneRect(-180, -90, 360, 180)
