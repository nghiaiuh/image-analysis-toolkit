from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QButtonGroup, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class AppSidebar(QWidget):
    pageRequested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("appSidebar")
        self.setMinimumWidth(164)
        self.setMaximumWidth(210)
        group = QButtonGroup(self)
        group.setExclusive(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(7)
        title = QLabel("IA  /  TOOLKIT")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        subtitle = QLabel("KHÔNG GIAN LÀM VIỆC ẢNH")
        subtitle.setObjectName("metadata")
        layout.addWidget(subtitle)
        layout.addSpacing(18)
        for index, (key, label) in enumerate((
            ("image", "◈  Image Studio"),
            ("counter", "◌  Cell Counter"),
            ("history", "◷  Lịch sử"),
            ("settings", "⚙  Cài đặt"),
        )):
            button = QPushButton(label)
            button.setObjectName("navButton")
            button.setCheckable(True)
            button.setChecked(index == 0)
            group.addButton(button)
            layout.addWidget(button)
            button.clicked.connect(lambda _checked=False, page=key: self.pageRequested.emit(page))
        layout.addStretch(1)
        status = QLabel("NATIVE • OPENCV")
        status.setObjectName("metadata")
        layout.addWidget(status)


class StatusStrip(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("statusStrip")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 5, 12, 5)
        self._label = QLabel("Sẵn sàng")
        self._label.setObjectName("metadata")
        layout.addWidget(self._label)
        layout.addStretch(1)

    def set_status(self, text: str) -> None:
        self._label.setText(text)

