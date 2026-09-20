from __future__ import annotations

import numpy as np
from PySide6.QtWidgets import QFormLayout, QLabel, QVBoxLayout, QWidget

from shared.ui.histogram_widget import HistogramWidget


class ResultAnalysisPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.metric_labels: dict[str, QLabel] = {}
        form = QFormLayout()
        for key in [
            "Kích thước gốc",
            "Kích thước sau xử lý",
            "Tỉ lệ / Góc xoay",
            "Phương pháp nội suy",
            "Bù viền / Cắt góc",
            "Vùng cắt / Tỉ lệ giữ",
            "Thời gian thực thi",
        ]:
            label = QLabel("-")
            label.setWordWrap(True)
            self.metric_labels[key] = label
            form.addRow(f"{key}:", label)

        self.histogram = HistogramWidget()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(form)
        layout.addWidget(self.histogram, 1)

    def update_metrics(self, operation: str, metadata: dict | None, original: np.ndarray | None, result: np.ndarray | None) -> None:
        metadata = metadata or {}
        self.metric_labels["Kích thước gốc"].setText(self._format_size(metadata.get("original_size")))
        self.metric_labels["Kích thước sau xử lý"].setText(self._format_size(metadata.get("output_size")))
        self.metric_labels["Phương pháp nội suy"].setText(str(metadata.get("interpolation", "-")))
        self.metric_labels["Thời gian thực thi"].setText(f'{metadata.get("processing_time_ms", 0.0):.2f} ms' if metadata else "-")

        if operation == "Zoom":
            self.metric_labels["Tỉ lệ / Góc xoay"].setText(f'{metadata.get("scale", 1.0):.2f}x')
            self.metric_labels["Bù viền / Cắt góc"].setText("Không áp dụng")
            self.metric_labels["Vùng cắt / Tỉ lệ giữ"].setText("Không áp dụng")
        elif operation == "Rotate":
            clipping = "Có (bị mất góc)" if metadata.get("clipping_occurs") else "Không bị cắt"
            self.metric_labels["Tỉ lệ / Góc xoay"].setText(f'{metadata.get("angle", 0):.0f}°')
            self.metric_labels["Bù viền / Cắt góc"].setText(f'{metadata.get("border_mode", "-")} | Cắt góc: {clipping}')
            self.metric_labels["Vùng cắt / Tỉ lệ giữ"].setText("Không áp dụng")
        else:
            retained = metadata.get("retained_percentage")
            rect = metadata.get("rect", (0, 0, 0, 0))
            retained_text = f"{retained:.1f}%" if retained is not None else "-"
            self.metric_labels["Tỉ lệ / Góc xoay"].setText("Không áp dụng")
            self.metric_labels["Bù viền / Cắt góc"].setText("Không áp dụng")
            self.metric_labels["Vùng cắt / Tỉ lệ giữ"].setText(f"{rect} (giữ lại {retained_text})")

        self.histogram.plot_images(original, result)

    @staticmethod
    def _format_size(size: tuple[int, int] | None) -> str:
        if not size:
            return "-"
        return f"{size[0]} x {size[1]} px"
