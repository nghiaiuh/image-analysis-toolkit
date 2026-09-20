from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import numpy as np
from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QSplitter,
    QMessageBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from apps.image_viewer.config import APP_NAME, APP_STYLESHEET, PROJECT_OUTPUT_DIR
from apps.image_viewer.processing.crop import CropResult, apply_crop
from apps.image_viewer.processing.rotate import RotationResult, apply_rotation
from apps.image_viewer.processing.zoom import ZoomResult, apply_zoom
from apps.image_viewer.ui.controls_panel import ControlsPanel
from apps.image_viewer.ui.explanation_panel import ExplanationPanel
from apps.image_viewer.ui.image_canvas import ImageCanvas
from apps.image_viewer.ui.result_analysis_panel import ResultAnalysisPanel
from shared.constants import IMAGE_FILTER, VIDEO_FILTER
from shared.image_io import load_image, save_image
from shared.image_utils import image_dimensions
from shared.validators import validate_image_array
from shared.ui.video_frame_dialog import VideoFrameSelectorDialog
from shared.ui.file_toolbar import FileToolbar


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1480, 920)
        self.setStyleSheet(APP_STYLESHEET)

        self.original_image: np.ndarray | None = None
        self.result_image: np.ndarray | None = None
        self.last_metadata: dict | None = None
        self.current_crop_rect: tuple[int, int, int, int] | None = None

        self.toolbar = FileToolbar(include_video=True)
        self.original_canvas = ImageCanvas("Ảnh gốc (Original)")
        self.result_canvas = ImageCanvas("Ảnh kết quả (Result)")
        self.controls_panel = ControlsPanel()
        self.explanation_panel = ExplanationPanel()
        self.analysis_panel = ResultAnalysisPanel()
        self.image_info = ExplanationPanel()
        self.image_info.text.setReadOnly(True)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.explanation_panel, "Giải thích thuật toán")
        self.tabs.addTab(self.analysis_panel, "Phân tích kết quả")
        self.tabs.addTab(self.image_info, "Thông tin ảnh")

        self.tabs.tabBar().setExpanding(True)
        self.tabs.tabBar().setUsesScrollButtons(False)
        self.tabs.setMinimumHeight(170)

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)
        main_layout.addWidget(self.toolbar)

        self.content_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.content_splitter.setChildrenCollapsible(False)
        self.original_canvas.setMinimumWidth(240)
        self.result_canvas.setMinimumWidth(240)
        self.controls_panel.setMinimumWidth(300)
        self.content_splitter.addWidget(self.original_canvas)
        self.content_splitter.addWidget(self.result_canvas)
        self.content_splitter.addWidget(self.controls_panel)
        self.content_splitter.setStretchFactor(0, 1)
        self.content_splitter.setStretchFactor(1, 1)
        self.content_splitter.setStretchFactor(2, 0)
        self.content_splitter.setSizes([520, 520, 340])

        self.workspace_splitter = QSplitter(Qt.Orientation.Vertical)
        self.workspace_splitter.setChildrenCollapsible(False)
        self.workspace_splitter.addWidget(self.content_splitter)
        self.workspace_splitter.addWidget(self.tabs)
        self.workspace_splitter.setStretchFactor(0, 1)
        self.workspace_splitter.setStretchFactor(1, 0)
        self.workspace_splitter.setSizes([620, 250])
        main_layout.addWidget(self.workspace_splitter, 1)
        QTimer.singleShot(0, self._stretch_tab_bar)

        self.toolbar.openImageRequested.connect(self.open_image)
        self.toolbar.openVideoRequested.connect(self.open_video)
        self.toolbar.saveRequested.connect(self.save_result)
        self.toolbar.resetRequested.connect(self.reset_all)
        self.controls_panel.operationChanged.connect(self._on_operation_changed)
        self.controls_panel.parametersChanged.connect(self._on_parameters_changed)
        self.controls_panel.cropApplied.connect(self._apply_crop_from_controls)
        self.controls_panel.cropReset.connect(self._reset_crop)
        self.original_canvas.cropRectChanged.connect(self._on_crop_selected)

        self._on_operation_changed(self.controls_panel.current_operation())
        self._refresh_image_info()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        QTimer.singleShot(0, self._stretch_tab_bar)

    def _stretch_tab_bar(self) -> None:
        width = self.tabs.width()
        if width > 2:
            self.tabs.tabBar().setFixedWidth(width - 2)

    def open_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", IMAGE_FILTER)
        if not path:
            return
        try:
            self._set_source_image(load_image(path))
            self.statusBar().showMessage(f"Loaded image: {Path(path).name}", 4000)
        except Exception as error:  # pragma: no cover - GUI interaction
            self._show_error(str(error))

    def open_video(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open Video", "", VIDEO_FILTER)
        if not path:
            return
        try:
            dialog = VideoFrameSelectorDialog(path, parent=self)
            if dialog.exec():
                frame, frame_index = dialog.selected_frame()
                if frame is not None:
                    self._set_source_image(frame)
                    self.statusBar().showMessage(
                        f"Loaded frame {frame_index + 1}/{dialog.metadata.frame_count} from {Path(path).name}",
                        5000,
                    )
        except Exception as error:  # pragma: no cover - GUI interaction
            self._show_error(str(error))

    def save_result(self) -> None:
        if self.result_image is None:
            self._show_error("There is no processed result to save.")
            return

        PROJECT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        default_name = self._default_output_name()
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Result",
            str(PROJECT_OUTPUT_DIR / default_name),
            IMAGE_FILTER,
        )
        if not path:
            return

        try:
            save_image(path, self.result_image)
            self.statusBar().showMessage(f"Saved result to {Path(path).name}", 4000)
        except Exception as error:  # pragma: no cover - GUI interaction
            self._show_error(str(error))

    def reset_all(self) -> None:
        self.result_image = self.original_image.copy() if self.original_image is not None else None
        self.current_crop_rect = None
        self.original_canvas.set_crop_rect(None)
        self.controls_panel.set_crop_values((0, 0, 0, 0))
        self._render_images()
        self._process_current_operation()

    def _set_source_image(self, image: np.ndarray) -> None:
        validate_image_array(image)
        self.original_image = image
        self.result_image = image.copy()
        self.current_crop_rect = None
        self.original_canvas.set_image(image)
        self.original_canvas.set_crop_rect(None)
        self.result_canvas.set_image(self.result_image)
        self._refresh_image_info()
        self._process_current_operation()

    def _on_operation_changed(self, operation: str) -> None:
        self.original_canvas.set_crop_enabled(operation == "Crop")
        self.explanation_panel.update_for_operation(operation, self.controls_panel.current_parameters(), self.last_metadata)
        self._process_current_operation()

    def _on_parameters_changed(self, operation: str, params: dict) -> None:
        self.explanation_panel.update_for_operation(operation, params, self.last_metadata)
        if operation != "Crop":
            self._process_current_operation()

    def _on_crop_selected(self, rect: tuple[int, int, int, int]) -> None:
        self.current_crop_rect = rect
        self.controls_panel.set_crop_values(rect)
        self._apply_crop_from_controls({"x": rect[0], "y": rect[1], "width": rect[2], "height": rect[3]})

    def _apply_crop_from_controls(self, params: dict) -> None:
        if self.original_image is None:
            return
        try:
            result = apply_crop(
                self.original_image,
                int(params["x"]),
                int(params["y"]),
                int(params["width"]),
                int(params["height"]),
            )
            self._apply_result("Crop", result)
            self.original_canvas.set_crop_rect(result.rect)
        except Exception as error:
            self._show_error(str(error))

    def _reset_crop(self) -> None:
        self.current_crop_rect = None
        self.original_canvas.set_crop_rect(None)
        self.controls_panel.set_crop_values((0, 0, 0, 0))
        if self.original_image is not None:
            self.result_image = self.original_image.copy()
            self.result_canvas.set_image(self.result_image)
        self.last_metadata = None
        self.analysis_panel.update_metrics("Crop", None, self.original_image, self.result_image)

    def _process_current_operation(self) -> None:
        if self.original_image is None:
            return

        operation = self.controls_panel.current_operation()
        params = self.controls_panel.current_parameters()

        try:
            if operation == "Zoom":
                result = apply_zoom(self.original_image, params["scale"], params["interpolation"])
            elif operation == "Rotate":
                result = apply_rotation(self.original_image, params["angle"], params["interpolation"], params["border_mode"])
            else:
                self.explanation_panel.update_for_operation(operation, params, self.last_metadata)
                return
            self._apply_result(operation, result)
        except Exception as error:
            self._show_error(str(error))

    def _apply_result(self, operation: str, result: ZoomResult | RotationResult | CropResult) -> None:
        self.result_image = result.image
        self.last_metadata = asdict(result)
        self._render_images()
        self.explanation_panel.update_for_operation(operation, self.controls_panel.current_parameters(), self.last_metadata)
        self.analysis_panel.update_metrics(operation, self.last_metadata, self.original_image, self.result_image)
        self._refresh_image_info()

    def _render_images(self) -> None:
        self.original_canvas.set_image(self.original_image)
        self.result_canvas.set_image(self.result_image)

    def _refresh_image_info(self) -> None:
        original_size = image_dimensions(self.original_image) if self.original_image is not None else None
        result_size = image_dimensions(self.result_image) if self.result_image is not None else None
        html = f"""
        <h3>Thông tin ảnh</h3>
        <p><b>Kích thước gốc:</b> {self._size_text(original_size)} px</p>
        <p><b>Kích thước kết quả:</b> {self._size_text(result_size)} px</p>
        <p><b>Số kênh màu gốc:</b> {self._channel_text(self.original_image)}</p>
        <p><b>Số kênh màu kết quả:</b> {self._channel_text(self.result_image)}</p>
        <p><b>Công cụ đang chọn:</b> {self.controls_panel.current_operation()}</p>
        """
        self.image_info.text.setHtml(html)

    def _default_output_name(self) -> str:
        operation = self.controls_panel.current_operation().lower()
        if operation == "zoom":
            return f"zoom_{self.controls_panel.zoom_scale.value():.2f}x_result.jpg".replace(".00", "")
        if operation == "rotate":
            angle = int(self.controls_panel.rotate_angle.value())
            return f"rotate_{angle}deg_result.jpg"
        return "crop_result.jpg"

    @staticmethod
    def _size_text(size: tuple[int, int] | None) -> str:
        return f"{size[0]} x {size[1]}" if size else "-"

    @staticmethod
    def _channel_text(image: np.ndarray | None) -> str:
        if image is None:
            return "-"
        return "1" if image.ndim == 2 else str(image.shape[2])

    def _show_error(self, message: str) -> None:
        QMessageBox.critical(self, APP_NAME, message)
