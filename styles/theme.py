from __future__ import annotations

from styles import colors


APP_STYLESHEET = f"""
* {{
    font-family: Inter, "Segoe UI", sans-serif;
    font-size: 13px;
    color: {colors.TEXT};
}}
QMainWindow, QWidget#appShell, QWidget#workspace, QWidget#pageSurface {{
    background: {colors.BACKGROUND};
}}
QWidget#topToolbar, QWidget#statusStrip {{
    background: {colors.BACKGROUND_SECONDARY};
    border: 1px solid {colors.BORDER};
    border-radius: 12px;
}}
QWidget#appSidebar {{
    background: {colors.BACKGROUND_SECONDARY};
    border-right: 1px solid {colors.BORDER};
}}
QWidget#panel, QGroupBox, QTabWidget::pane {{
    background: {colors.PANEL};
    border: 1px solid {colors.BORDER};
    border-radius: 12px;
}}
QGroupBox {{
    margin-top: 10px;
    padding: 13px;
    font-weight: 600;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
    color: {colors.TEXT_SECONDARY};
}}
QLabel#appTitle {{ font-size: 20px; font-weight: 600; }}
QLabel#pageTitle {{ font-size: 18px; font-weight: 600; }}
QLabel#sectionTitle, QLabel#panelTitle {{ font-size: 14px; font-weight: 600; }}
QLabel#metadata, QLabel#canvasMetadata {{ color: {colors.TEXT_SECONDARY}; font-size: 11px; }}
QLabel#technicalValue {{ font-family: "Cascadia Code", "JetBrains Mono", monospace; color: {colors.TEXT_SECONDARY}; }}
QLabel#kpiValue {{ font-size: 27px; font-weight: 600; color: {colors.TEXT}; }}
QLabel#kpiCaption {{ color: {colors.TEXT_SECONDARY}; font-size: 11px; }}

QPushButton {{
    min-height: 30px;
    padding: 0 11px;
    background: {colors.SURFACE};
    border: 1px solid {colors.BORDER};
    border-radius: 8px;
}}
QPushButton:hover {{ background: {colors.SURFACE_HOVER}; border-color: {colors.BORDER_STRONG}; }}
QPushButton:pressed {{ background: #102237; }}
QPushButton:disabled {{ color: {colors.TEXT_MUTED}; background: #101821; border-color: transparent; }}
QPushButton#accentButton, QPushButton#runButton {{
    color: white;
    font-weight: 600;
    background: #258DFF;
    border-color: #3EA5FF;
}}
QPushButton#accentButton:hover, QPushButton#runButton:hover {{ background: #20A7FF; }}
QPushButton#navButton {{
    text-align: left;
    color: {colors.TEXT_SECONDARY};
    border: 1px solid transparent;
    background: transparent;
    padding: 0 12px;
}}
QPushButton#navButton:hover {{ background: rgba(47, 155, 255, 0.08); color: {colors.TEXT}; }}
QPushButton#navButton:checked {{
    background: rgba(47, 155, 255, 0.15);
    border-color: rgba(34, 211, 238, 0.22);
    color: {colors.CYAN};
}}
QPushButton#segmentButton {{ border-radius: 7px; background: transparent; color: {colors.TEXT_SECONDARY}; }}
QPushButton#segmentButton:checked {{ color: {colors.TEXT}; background: rgba(47, 155, 255, 0.18); border-color: rgba(47, 155, 255, 0.35); }}

QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    min-height: 30px;
    padding: 0 9px;
    background: {colors.SURFACE};
    border: 1px solid {colors.BORDER};
    border-radius: 7px;
    selection-background-color: {colors.ACCENT};
}}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{ border-color: {colors.ACCENT}; }}
QComboBox::drop-down {{ border: 0; width: 22px; }}
QComboBox QAbstractItemView {{ background: {colors.SURFACE}; border: 1px solid {colors.BORDER_STRONG}; selection-background-color: rgba(47, 155, 255, 0.22); }}

QTabBar::tab {{ color: {colors.TEXT_SECONDARY}; background: transparent; padding: 8px 11px; border: 0; }}
QTabBar::tab:selected {{ color: {colors.TEXT}; border-bottom: 2px solid {colors.CYAN}; }}
QTextEdit, QListWidget, QTableWidget, QScrollArea {{ background: {colors.PANEL}; border: 1px solid {colors.BORDER}; border-radius: 10px; }}
QTextBrowser#algorithmExplanation {{ background: {colors.PANEL}; border: 1px solid {colors.BORDER}; border-radius: 10px; padding: 8px; }}
QHeaderView::section {{ background: {colors.SURFACE}; color: {colors.TEXT_SECONDARY}; padding: 7px; border: 0; border-bottom: 1px solid {colors.BORDER}; }}
QTableWidget {{ gridline-color: rgba(120, 170, 220, 0.07); selection-background-color: rgba(47, 155, 255, 0.18); }}
QCheckBox {{ spacing: 8px; color: {colors.TEXT_SECONDARY}; }}
QCheckBox::indicator {{ width: 15px; height: 15px; border: 1px solid {colors.BORDER_STRONG}; border-radius: 4px; background: {colors.SURFACE}; }}
QCheckBox::indicator:checked {{ background: {colors.ACCENT}; border-color: {colors.ACCENT}; }}
QSlider::groove:horizontal {{ height: 3px; background: rgba(120, 170, 220, 0.18); border-radius: 2px; }}
QSlider::sub-page:horizontal {{ background: {colors.ACCENT}; border-radius: 2px; }}
QSlider::handle:horizontal {{ width: 12px; height: 12px; margin: -5px 0; border-radius: 6px; background: {colors.CYAN}; }}
QScrollBar:vertical {{ width: 6px; background: transparent; margin: 4px; }}
QScrollBar::handle:vertical {{ min-height: 24px; border-radius: 3px; background: rgba(120,160,200,0.30); }}
QScrollBar::handle:vertical:hover {{ background: rgba(80,170,255,0.55); }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QToolTip {{ background: {colors.SURFACE}; border: 1px solid {colors.BORDER_STRONG}; border-radius: 6px; padding: 6px 8px; color: {colors.TEXT}; }}
"""
