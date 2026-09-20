from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from apps.image_viewer.config import DEFAULT_INTERPOLATION, DEFAULT_ROTATION_ANGLE, DEFAULT_ROTATION_BORDER, DEFAULT_SCALE
from shared.ui.parameter_slider import ParameterSlider


class ControlsPanel(QWidget):
    operationChanged = Signal(str)
    parametersChanged = Signal(str, dict)
    cropApplied = Signal(dict)
    cropReset = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.operation_combo = QComboBox()
        self.operation_combo.addItems(["Zoom", "Rotate", "Crop"])

        operation_box = QGroupBox("Công cụ")
        operation_layout = QVBoxLayout(operation_box)
        operation_layout.addWidget(QLabel("Chọn thao tác:"))
        operation_layout.addWidget(self.operation_combo)

        self.stacked = QStackedWidget()
        self.zoom_page = self._build_zoom_page()
        self.rotate_page = self._build_rotate_page()
        self.crop_page = self._build_crop_page()
        self.stacked.addWidget(self.zoom_page)
        self.stacked.addWidget(self.rotate_page)
        self.stacked.addWidget(self.crop_page)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.addWidget(operation_box)
        self.stacked.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self.settings_scroll = QScrollArea()
        self.settings_scroll.setWidgetResizable(True)
        self.settings_scroll.setMinimumHeight(0)
        self.settings_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.settings_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.settings_scroll.setWidget(self.stacked)
        layout.addWidget(self.settings_scroll, 1)

        self.operation_combo.currentIndexChanged.connect(self.stacked.setCurrentIndex)
        self.operation_combo.currentTextChanged.connect(self.operationChanged.emit)
        self.operation_combo.currentTextChanged.connect(lambda _: self._emit_current_parameters())

    def current_operation(self) -> str:
        return self.operation_combo.currentText()

    def set_crop_values(self, rect: tuple[int, int, int, int]) -> None:
        x, y, width, height = rect
        for widget, value in zip((self.crop_x, self.crop_y, self.crop_width, self.crop_height), (x, y, width, height)):
            widget.blockSignals(True)
            widget.setValue(value)
            widget.blockSignals(False)

    def crop_rect(self) -> tuple[int, int, int, int]:
        return (
            self.crop_x.value(),
            self.crop_y.value(),
            self.crop_width.value(),
            self.crop_height.value(),
        )

    def _build_zoom_page(self) -> QWidget:
        page = QWidget()
        box = QGroupBox("Cài đặt Zoom")
        self.zoom_scale = ParameterSlider("Tỉ lệ (Scale)", 0.25, 4.0, DEFAULT_SCALE, step=0.05, decimals=2)
        self.zoom_interpolation = QComboBox()
        self.zoom_interpolation.addItems(["Nearest Neighbor", "Bilinear", "Bicubic"])
        self.zoom_interpolation.setCurrentText(DEFAULT_INTERPOLATION)
        self.zoom_reset = QPushButton("Đặt lại Zoom")

        layout = QVBoxLayout(box)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        layout.addWidget(self.zoom_scale)
        layout.addWidget(QLabel("Phương pháp nội suy:"))
        layout.addWidget(self.zoom_interpolation)
        layout.addWidget(self.zoom_reset)

        page_layout = QVBoxLayout(page)
        page_layout.addWidget(box)
        page_layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)

        self.zoom_scale.valueChanged.connect(lambda _: self._emit_current_parameters())
        self.zoom_interpolation.currentTextChanged.connect(lambda _: self._emit_current_parameters())
        self.zoom_reset.clicked.connect(self._reset_zoom)
        return page

    def _build_rotate_page(self) -> QWidget:
        page = QWidget()
        box = QGroupBox("Cài đặt Xoay")
        self.rotate_angle = ParameterSlider("Góc xoay (Angle)", -180, 180, DEFAULT_ROTATION_ANGLE, step=1.0, decimals=0)
        self.rotate_interpolation = QComboBox()
        self.rotate_interpolation.addItems(["Nearest Neighbor", "Bilinear", "Bicubic"])
        self.rotate_interpolation.setCurrentText(DEFAULT_INTERPOLATION)
        self.rotate_border = QComboBox()
        self.rotate_border.addItems(["Constant Black", "Replicate", "Reflect"])
        self.rotate_border.setCurrentText(DEFAULT_ROTATION_BORDER)

        shortcuts = QGridLayout()
        self.left_90_button = QPushButton("Xoay trái 90°")
        self.right_90_button = QPushButton("Xoay phải 90°")
        self.ccw_button = QPushButton("-15°")
        self.cw_button = QPushButton("+15°")
        self.rotate_reset = QPushButton("Đặt lại góc xoay")
        for control in (
            self.rotate_interpolation,
            self.rotate_border,
            self.left_90_button,
            self.right_90_button,
            self.ccw_button,
            self.cw_button,
            self.rotate_reset,
        ):
            control.setMinimumHeight(32)
        shortcuts.setRowMinimumHeight(0, 32)
        shortcuts.setRowMinimumHeight(1, 32)
        shortcuts.addWidget(self.left_90_button, 0, 0)
        shortcuts.addWidget(self.right_90_button, 0, 1)
        shortcuts.addWidget(self.ccw_button, 1, 0)
        shortcuts.addWidget(self.cw_button, 1, 1)

        layout = QVBoxLayout(box)
        layout.setSpacing(8)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        layout.addWidget(self.rotate_angle)
        layout.addWidget(QLabel("Phương pháp nội suy:"))
        layout.addWidget(self.rotate_interpolation)
        layout.addWidget(QLabel("Chế độ bù viền:"))
        layout.addWidget(self.rotate_border)
        layout.addLayout(shortcuts)
        layout.addWidget(self.rotate_reset)

        page_layout = QVBoxLayout(page)
        page_layout.addWidget(box)
        page_layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)

        self.rotate_angle.valueChanged.connect(lambda _: self._emit_current_parameters())
        self.rotate_interpolation.currentTextChanged.connect(lambda _: self._emit_current_parameters())
        self.rotate_border.currentTextChanged.connect(lambda _: self._emit_current_parameters())
        self.left_90_button.clicked.connect(lambda: self._nudge_rotation(-90))
        self.right_90_button.clicked.connect(lambda: self._nudge_rotation(90))
        self.ccw_button.clicked.connect(lambda: self._nudge_rotation(-15))
        self.cw_button.clicked.connect(lambda: self._nudge_rotation(15))
        self.rotate_reset.clicked.connect(self._reset_rotation)
        return page

    def _build_crop_page(self) -> QWidget:
        page = QWidget()
        box = QGroupBox("Cài đặt Cắt (Crop)")
        form = QFormLayout()
        self.crop_x = QSpinBox()
        self.crop_y = QSpinBox()
        self.crop_width = QSpinBox()
        self.crop_height = QSpinBox()
        for widget in (self.crop_x, self.crop_y, self.crop_width, self.crop_height):
            widget.setRange(0, 100000)
            widget.valueChanged.connect(lambda _: self._emit_current_parameters())
        form.addRow("X:", self.crop_x)
        form.addRow("Y:", self.crop_y)
        form.addRow("Rộng (Width):", self.crop_width)
        form.addRow("Cao (Height):", self.crop_height)

        buttons = QHBoxLayout()
        self.crop_apply = QPushButton("Áp dụng cắt")
        self.crop_apply.setObjectName("accentButton")
        self.crop_reset = QPushButton("Đặt lại vùng cắt")
        buttons.addWidget(self.crop_apply)
        buttons.addWidget(self.crop_reset)

        help_label = QLabel("Mẹo: Bạn có thể kéo chuột trực tiếp trên ảnh gốc để chọn vùng cần cắt.")
        help_label.setWordWrap(True)

        layout = QVBoxLayout(box)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        layout.addLayout(form)
        layout.addWidget(help_label)
        layout.addLayout(buttons)

        page_layout = QVBoxLayout(page)
        page_layout.addWidget(box)
        page_layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)

        self.crop_apply.clicked.connect(lambda: self.cropApplied.emit(self._current_crop_parameters()))
        self.crop_reset.clicked.connect(self.cropReset.emit)
        return page

    def _emit_current_parameters(self) -> None:
        self.parametersChanged.emit(self.current_operation(), self.current_parameters())

    def current_parameters(self) -> dict:
        if self.current_operation() == "Zoom":
            return {
                "scale": self.zoom_scale.value(),
                "interpolation": self.zoom_interpolation.currentText(),
            }
        if self.current_operation() == "Rotate":
            return {
                "angle": self.rotate_angle.value(),
                "interpolation": self.rotate_interpolation.currentText(),
                "border_mode": self.rotate_border.currentText(),
            }
        return self._current_crop_parameters()

    def _current_crop_parameters(self) -> dict:
        x, y, width, height = self.crop_rect()
        return {"x": x, "y": y, "width": width, "height": height}

    def _reset_zoom(self) -> None:
        self.zoom_scale.set_value(DEFAULT_SCALE)
        self.zoom_interpolation.setCurrentText(DEFAULT_INTERPOLATION)
        self._emit_current_parameters()

    def _reset_rotation(self) -> None:
        self.rotate_angle.set_value(DEFAULT_ROTATION_ANGLE)
        self.rotate_interpolation.setCurrentText(DEFAULT_INTERPOLATION)
        self.rotate_border.setCurrentText(DEFAULT_ROTATION_BORDER)
        self._emit_current_parameters()

    def _nudge_rotation(self, delta: float) -> None:
        new_value = max(-180, min(180, self.rotate_angle.value() + delta))
        self.rotate_angle.set_value(new_value)
        self._emit_current_parameters()

