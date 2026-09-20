from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QSlider, QSpinBox, QVBoxLayout, QWidget

from shared.image_utils import numpy_to_qpixmap, scale_pixmap_for_viewport
from shared.ui.interaction import install_drag_first_parameter_behavior
from shared.video_io import VideoInfo, get_video_metadata


class VideoFrameSelectorDialog(QDialog):
    """Preview a video and return the user-selected frame without changing the main editor UI."""

    def __init__(self, video_path: str | Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        install_drag_first_parameter_behavior()
        self.video_path = Path(video_path)
        self.metadata: VideoInfo = get_video_metadata(self.video_path)
        self.current_frame: np.ndarray | None = None
        self.current_frame_index = 0
        self._capture = cv2.VideoCapture(str(self.video_path))
        if not self._capture.isOpened():
            raise ValueError(f"Unable to open video: {self.video_path}")
        self.setWindowTitle(f"Select Video Frame — {self.video_path.name}")
        self.resize(780, 600)
        self.setMinimumSize(540, 420)
        self._build_ui()
        self._load_frame(0)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        duration = self._format_time(self.metadata.duration_seconds)
        info = QLabel(
            f"<b>{self.video_path.name}</b>  ·  {self.metadata.width} × {self.metadata.height}  ·  "
            f"{self.metadata.frame_count} frames  ·  {self.metadata.fps:.1f} FPS  ·  {duration}"
        )
        info.setObjectName("metadata")
        info.setWordWrap(True)
        layout.addWidget(info)

        self.preview = QLabel("Loading frame…")
        self.preview.setObjectName("imageViewport")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumSize(480, 270)
        layout.addWidget(self.preview, 1)

        self.frame_label = QLabel()
        self.frame_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.frame_label.setObjectName("technicalValue")
        layout.addWidget(self.frame_label)

        frame_controls = QHBoxLayout()
        max_frame = max(0, self.metadata.frame_count - 1)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, max_frame)
        self.spinbox = QSpinBox()
        self.spinbox.setRange(0, max_frame)
        self.spinbox.setFixedWidth(90)
        frame_controls.addWidget(QLabel("Frame"))
        frame_controls.addWidget(self.slider, 1)
        frame_controls.addWidget(self.spinbox)
        layout.addLayout(frame_controls)

        navigation = QHBoxLayout()
        frame_jump = max(1, round(self.metadata.fps))
        for label, delta in (("−1 s", -frame_jump), ("−1 frame", -1), ("+1 frame", 1), ("+1 s", frame_jump)):
            button = QPushButton(label)
            button.clicked.connect(lambda _checked=False, step=delta: self._jump(step))
            navigation.addWidget(button)
        layout.addLayout(navigation)

        actions = QHBoxLayout()
        actions.addStretch(1)
        cancel = QPushButton("Cancel")
        select = QPushButton("Use This Frame")
        select.setObjectName("accentButton")
        cancel.clicked.connect(self.reject)
        select.clicked.connect(self.accept)
        actions.addWidget(cancel)
        actions.addWidget(select)
        layout.addLayout(actions)

        self.slider.valueChanged.connect(self._set_frame_from_slider)
        self.spinbox.valueChanged.connect(self._set_frame_from_spinbox)

    def _set_frame_from_slider(self, index: int) -> None:
        if self.spinbox.value() != index:
            self.spinbox.blockSignals(True)
            self.spinbox.setValue(index)
            self.spinbox.blockSignals(False)
        self._load_frame(index)

    def _set_frame_from_spinbox(self, index: int) -> None:
        if self.slider.value() != index:
            self.slider.blockSignals(True)
            self.slider.setValue(index)
            self.slider.blockSignals(False)
        self._load_frame(index)

    def _jump(self, delta: int) -> None:
        self.slider.setValue(max(0, min(self.slider.maximum(), self.slider.value() + delta)))

    def _load_frame(self, index: int) -> None:
        self._capture.set(cv2.CAP_PROP_POS_FRAMES, index)
        success, frame = self._capture.read()
        if not success or frame is None:
            self.preview.setText("Unable to read this frame.")
            return
        self.current_frame = frame
        self.current_frame_index = index
        self._render_preview()
        timestamp = index / self.metadata.fps if self.metadata.fps else 0.0
        self.frame_label.setText(f"Frame {index + 1} / {self.metadata.frame_count}  ·  {self._format_time(timestamp)}")

    def _render_preview(self) -> None:
        if self.current_frame is None:
            return
        pixmap = numpy_to_qpixmap(self.current_frame)
        self.preview.setPixmap(scale_pixmap_for_viewport(pixmap, self.preview.size(), self.devicePixelRatioF()))

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._render_preview()

    def accept(self) -> None:
        self._release_capture()
        super().accept()

    def reject(self) -> None:
        self._release_capture()
        super().reject()

    def closeEvent(self, event) -> None:  # noqa: N802
        self._release_capture()
        super().closeEvent(event)

    def selected_frame(self) -> tuple[np.ndarray | None, int]:
        return self.current_frame, self.current_frame_index

    def _release_capture(self) -> None:
        if self._capture.isOpened():
            self._capture.release()

    @staticmethod
    def _format_time(seconds: float) -> str:
        minutes = int(seconds // 60)
        return f"{minutes:02d}:{seconds % 60:05.2f}"
