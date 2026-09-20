from __future__ import annotations

from PySide6.QtCore import QEvent, QObject
from PySide6.QtWidgets import (
    QAbstractScrollArea,
    QAbstractSlider,
    QAbstractSpinBox,
    QApplication,
    QComboBox,
    QScrollBar,
)


def _scroll_ancestor(widget: QObject) -> QAbstractScrollArea | None:
    current = widget.parent()
    while current is not None:
        if isinstance(current, QAbstractScrollArea):
            return current
        current = current.parent()
    return None


def _scroll_by_wheel(scroll_area: QAbstractScrollArea, delta: int) -> None:
    scrollbar = scroll_area.verticalScrollBar()
    if not delta or scrollbar.maximum() == scrollbar.minimum():
        return
    steps = max(1, abs(delta) // 120)
    direction = -1 if delta > 0 else 1
    scrollbar.setValue(scrollbar.value() + direction * steps * scrollbar.singleStep())


class _DragFirstInputFilter(QObject):
    """Prevents accidental parameter changes while a scroll area is being read."""

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:  # noqa: N802
        is_parameter = isinstance(watched, (QAbstractSlider, QAbstractSpinBox, QComboBox)) and not isinstance(watched, QScrollBar)
        if event.type() == QEvent.Type.Wheel and is_parameter:
            scroll_area = _scroll_ancestor(watched)
            if scroll_area is not None:
                _scroll_by_wheel(scroll_area, event.angleDelta().y())
            event.accept()
            return True
        return super().eventFilter(watched, event)


def install_drag_first_parameter_behavior() -> None:
    """Install once per QApplication; sliders remain fully adjustable by dragging."""

    app = QApplication.instance()
    if app is None or getattr(app, "_drag_first_parameter_filter", None) is not None:
        return
    input_filter = _DragFirstInputFilter(app)
    app.installEventFilter(input_filter)
    app._drag_first_parameter_filter = input_filter  # type: ignore[attr-defined]
