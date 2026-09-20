from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QDoubleSpinBox, QHBoxLayout, QLabel, QSlider, QVBoxLayout, QWidget

from shared.ui.interaction import install_drag_first_parameter_behavior


class ParameterSlider(QWidget):
    valueChanged = Signal(float)

    def __init__(
        self,
        label: str,
        minimum: float,
        maximum: float,
        value: float,
        step: float = 1.0,
        decimals: int = 0,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        install_drag_first_parameter_behavior()
        self.minimum = minimum
        self.maximum = maximum
        self.step = step
        self.steps_count = int(round((maximum - minimum) / step))

        self.label = QLabel(label)
        self.value_label = QLabel()
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.spinbox = QDoubleSpinBox()

        self.slider.setRange(0, self.steps_count)
        self.spinbox.setRange(minimum, maximum)
        self.spinbox.setSingleStep(step)
        self.spinbox.setDecimals(decimals)

        top = QHBoxLayout()
        top.addWidget(self.label)
        top.addStretch(1)
        top.addWidget(self.value_label)

        controls = QHBoxLayout()
        controls.addWidget(self.slider, 1)
        controls.addWidget(self.spinbox)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(top)
        layout.addLayout(controls)

        self.slider.valueChanged.connect(self._on_slider_changed)
        self.spinbox.valueChanged.connect(self._on_spinbox_changed)
        self.set_value(value)

    def value(self) -> float:
        return self.spinbox.value()

    def set_value(self, value: float) -> None:
        clamped = max(self.minimum, min(self.maximum, value))
        slider_value = int(round((clamped - self.minimum) / self.step))
        self.slider.blockSignals(True)
        self.spinbox.blockSignals(True)
        self.slider.setValue(slider_value)
        self.spinbox.setValue(clamped)
        self.slider.blockSignals(False)
        self.spinbox.blockSignals(False)
        self.value_label.setText(f"{clamped:.2f}".rstrip("0").rstrip("."))

    def _on_slider_changed(self, slider_value: int) -> None:
        value = self.minimum + (slider_value * self.step)
        self.set_value(value)
        self.valueChanged.emit(value)

    def _on_spinbox_changed(self, value: float) -> None:
        self.set_value(value)
        self.valueChanged.emit(value)
