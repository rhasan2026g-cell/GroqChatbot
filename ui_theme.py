"""Shared visual language for GroqChatbot.

Everything the desktop UI needs to look consistent lives here: palettes,
the Qt stylesheet, the gradient logo, the splash artwork and the app icon.
Keeping it in one module means the chat window and every dialog stay in sync.
"""

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QIcon,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPalette,
    QPen,
    QPixmap,
    QRadialGradient,
)

from app_paths import DATA_DIR

APP_VERSION = "1.1.0"
APP_TAGLINE = "Local-first AI agent · memory · RAG · creation studio"


def _check_icon(color: str) -> str:
    """Write a tiny SVG check mark so styled checkboxes stay unambiguous."""
    folder = Path(DATA_DIR) / "ui"
    try:
        folder.mkdir(parents=True, exist_ok=True)
    except OSError:
        return ""
    path = folder / f"check-{color.strip('#').lower()}.svg"
    try:
        if not path.exists():
            path.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" '
                'viewBox="0 0 16 16"><path d="M3.4 8.4l3.1 3.1 6.1-6.6" fill="none" '
                f'stroke="{color}" stroke-width="2.1" stroke-linecap="round" '
                'stroke-linejoin="round"/></svg>',
                encoding="utf-8",
            )
    except OSError:
        return ""
    return path.as_posix()

ACCENTS = {
    "blue": ("#4c8dff", "#8b5cf6"),
    "violet": ("#8b5cf6", "#ec4899"),
    "emerald": ("#10b981", "#22d3ee"),
    "amber": ("#f59e0b", "#ef4444"),
    "rose": ("#f43f5e", "#8b5cf6"),
}

PALETTES = {
    "dark": {
        "bg": "#0b0f16",
        "panel": "#121925",
        "panel2": "#182233",
        "panel3": "#1e2a3d",
        "border": "#243047",
        "border2": "#31415c",
        "text": "#e6edf8",
        "muted": "#8a98ad",
        "faint": "#5f6f86",
        "accent": "#4c8dff",
        "accent2": "#8b5cf6",
        "accent_text": "#061020",
        "user_card": "#173a63",
        "user_border": "#2b5a91",
        "bot_card": "#141d2b",
        "error_card": "#35181d",
        "error_border": "#6b2a32",
        "success": "#34d399",
        "warning": "#fbbf24",
        "danger": "#f87171",
        "code_bg": "#080c12",
        "code_text": "#a8d4ff",
        "selection": "#2d4f80",
        "shadow": "#000000",
    },
    "light": {
        "bg": "#f3f6fb",
        "panel": "#ffffff",
        "panel2": "#eef3fa",
        "panel3": "#e3ebf6",
        "border": "#d6e0ed",
        "border2": "#bccbe0",
        "text": "#16202e",
        "muted": "#5d6f87",
        "faint": "#8494a9",
        "accent": "#2563eb",
        "accent2": "#7c3aed",
        "accent_text": "#ffffff",
        "user_card": "#dbeafe",
        "user_border": "#9dc4f7",
        "bot_card": "#ffffff",
        "error_card": "#fee2e2",
        "error_border": "#fca5a5",
        "success": "#047857",
        "warning": "#b45309",
        "danger": "#b91c1c",
        "code_bg": "#eef2f8",
        "code_text": "#1d4ed8",
        "selection": "#bfdbfe",
        "shadow": "#94a3b8",
    },
}


def palette(theme: str = "dark", accent: str = "blue") -> dict:
    """Return a complete palette for the requested theme and accent."""
    base = dict(PALETTES.get(theme, PALETTES["dark"]))
    a1, a2 = ACCENTS.get(accent, ACCENTS["blue"])
    base["accent"] = a1
    base["accent2"] = a2
    base["accent_soft"] = _mix(a1, base["panel"], 0.18)
    base["accent_glow"] = _mix(a1, base["panel"], 0.35)
    return base


def _mix(color: str, other: str, amount: float) -> str:
    """Blend two hex colours. amount=0 -> color, 1 -> other."""
    try:
        c1 = QColor(color)
        c2 = QColor(other)
        r = int(c1.red() * (1 - amount) + c2.red() * amount)
        g = int(c1.green() * (1 - amount) + c2.green() * amount)
        b = int(c1.blue() * (1 - amount) + c2.blue() * amount)
        return QColor(r, g, b).name()
    except Exception:
        return color


def make_qt_palette(p: dict) -> QPalette:
    """A real QPalette matching the stylesheet.

    Without this, native-painted widgets (scroll area viewports, menus, tooltips,
    disabled text) keep the operating system palette — which is dark when Windows
    uses dark mode, even while the app is showing its light theme.
    """
    pal = QPalette()
    roles = {
        QPalette.Window: p["bg"],
        QPalette.WindowText: p["text"],
        QPalette.Base: p["panel"],
        QPalette.AlternateBase: p["panel2"],
        QPalette.ToolTipBase: p["panel2"],
        QPalette.ToolTipText: p["text"],
        QPalette.Text: p["text"],
        QPalette.Button: p["panel"],
        QPalette.ButtonText: p["text"],
        QPalette.BrightText: p["danger"],
        QPalette.Link: p["accent"],
        QPalette.Highlight: p["accent"],
        QPalette.HighlightedText: p["accent_text"],
        QPalette.PlaceholderText: p["faint"],
        QPalette.Light: p["panel3"],
        QPalette.Midlight: p["border2"],
        QPalette.Mid: p["border"],
        QPalette.Dark: p["border2"],
        QPalette.Shadow: p["shadow"],
    }
    for role, color in roles.items():
        try:
            pal.setColor(role, QColor(color))
        except Exception:
            pass
    for role in (QPalette.WindowText, QPalette.Text, QPalette.ButtonText):
        pal.setColor(QPalette.Disabled, role, QColor(p["faint"]))
    return pal


def build_stylesheet(p: dict, compact: bool = False) -> str:
    """A complete, self-contained Qt stylesheet for the whole application."""
    pad = 6 if compact else 10
    check = _check_icon(p["accent_text"])
    return f"""
    QMainWindow, QDialog {{ background-color: {p['bg']}; color: {p['text']}; }}
    QWidget {{ color: {p['text']}; font-size: 12.5px; }}
    QWidget#root, QWidget#canvas, QScrollArea#scroll {{ background-color: {p['bg']}; }}
    QFrame#header, QFrame#footer, QFrame#sidebar {{
        background-color: {p['panel']};
    }}
    QFrame#header {{ border-bottom: 1px solid {p['border']}; }}
    QFrame#footer {{ border-top: 1px solid {p['border']}; }}
    QFrame#sidebar {{ border-left: 1px solid {p['border']}; }}
    QScrollArea#sidebarScroll, QScrollArea#sidebarScroll > QWidget,
    QScrollArea#sidebarScroll > QWidget > QWidget {{
        background-color: {p['panel']}; border: none;
    }}

    QLabel#appTitle {{ color: {p['text']}; font-size: 15px; font-weight: 700; }}
    QLabel#tagline {{ color: {p['muted']}; font-size: 10.5px; }}
    QLabel#status {{ color: {p['muted']}; font-size: 11px; }}
    QLabel#stats {{ color: {p['faint']}; font-size: 10.5px; }}
    QLabel#welcomeTitle {{ color: {p['text']}; font-size: 23px; font-weight: 700; }}
    QLabel#welcomeSub {{ color: {p['muted']}; font-size: 13px; }}
    QLabel#sectionTitle {{
        color: {p['muted']}; font-size: 10px; font-weight: 700;
        letter-spacing: 1.2px;
    }}
    QLabel#cardTitle {{ color: {p['text']}; font-size: 12.5px; font-weight: 600; }}
    QLabel#cardValue {{ color: {p['text']}; font-size: 18px; font-weight: 700; }}
    QLabel#cardHint {{ color: {p['muted']}; font-size: 10.5px; }}
    QLabel#dlgTitle {{ color: {p['text']}; font-size: 17px; font-weight: 700; }}
    QLabel#dlgBody {{ color: {p['muted']}; font-size: 12.5px; }}
    QLabel#dlgMeta {{ color: {p['muted']}; font-size: 11.5px; }}
    QLabel#dlgSteps {{ color: {p['text']}; font-size: 12.5px; }}
    QLabel#dlgError {{
        background-color: {p['error_card']}; border: 1px solid {p['error_border']};
        border-radius: 8px; color: {p['danger']}; font-size: 12px; padding: 8px 10px;
    }}
    QLabel#pill {{
        background: {p['panel3']}; border: 1px solid {p['border']};
        border-radius: 9px; color: {p['muted']}; font-size: 10px; padding: 2px 7px;
    }}

    QMenuBar {{ background: {p['panel']}; color: {p['text']}; border-bottom: 1px solid {p['border']}; }}
    QMenuBar::item {{ background: transparent; padding: 5px 9px; }}
    QMenuBar::item:selected {{ background: {p['panel3']}; border-radius: 5px; }}
    QMenu {{ background: {p['panel2']}; color: {p['text']}; border: 1px solid {p['border']}; padding: 5px; }}
    QMenu::item {{ padding: 6px 26px 6px 24px; border-radius: 5px; }}
    QMenu::item:selected {{ background: {p['accent_glow']}; }}
    QMenu::separator {{ height: 1px; background: {p['border']}; margin: 4px 8px; }}

    QFrame#userCard {{
        background-color: {p['user_card']}; border: 1px solid {p['user_border']};
        border-radius: 14px;
    }}
    QFrame#botCard {{
        background-color: {p['bot_card']}; border: 1px solid {p['border']};
        border-radius: 14px;
    }}
    QFrame#errorCard {{
        background-color: {p['error_card']}; border: 1px solid {p['error_border']};
        border-radius: 14px;
    }}
    QFrame#toolCard {{
        background-color: {p['panel2']}; border: 1px solid {p['border']};
        border-radius: 10px;
    }}
    QLabel#bubbleBody {{ color: {p['text']}; font-size: 13px; background: transparent; }}

    QPushButton {{
        background-color: {p['panel3']}; color: {p['text']};
        border: 1px solid {p['border2']}; border-radius: 9px;
        padding: 7px 12px; font-size: 12px;
    }}
    QPushButton:hover {{ background-color: {p['accent_glow']}; border-color: {p['accent']}; }}
    QPushButton:pressed {{ background-color: {p['accent_soft']}; }}
    QPushButton:disabled {{ color: {p['faint']}; background-color: {p['panel2']}; }}
    QPushButton#primary {{
        background-color: {p['accent']}; color: {p['accent_text']};
        border: none; font-weight: 700;
    }}
    QPushButton#primary:hover {{ background-color: {p['accent2']}; }}
    QPushButton#primary:disabled {{ background-color: {p['panel3']}; color: {p['faint']}; }}
    QPushButton#send {{
        background-color: {p['accent']}; color: {p['accent_text']};
        border: none; border-radius: 12px; font-size: 13px; font-weight: 700;
    }}
    QPushButton#send:hover {{ background-color: {p['accent2']}; }}
    QPushButton#send:disabled {{ background-color: {p['panel3']}; color: {p['faint']}; }}
    QPushButton#connect {{
        background-color: {p['accent']}; color: {p['accent_text']};
        border: none; border-radius: 10px; padding: 10px 22px;
        font-size: 13px; font-weight: 700;
    }}
    QPushButton#connect:hover {{ background-color: {p['accent2']}; }}
    QPushButton#copyBtn {{
        background: transparent; border: none; color: {p['muted']};
        font-size: 10px; padding: 1px 6px; border-radius: 5px;
    }}
    QPushButton#copyBtn:hover {{ color: {p['accent']}; background: {p['panel3']}; }}
    QPushButton#iconBtn {{
        background: transparent; border: 1px solid transparent; border-radius: 8px;
        font-size: 15px; padding: 0;
    }}
    QPushButton#iconBtn:hover {{ background: {p['panel3']}; border-color: {p['border']}; }}
    QPushButton#iconBtn:checked {{ background: {p['accent_soft']}; border-color: {p['accent']}; }}
    QPushButton#chip {{
        background-color: transparent; color: {p['text']};
        border: 1px solid {p['border2']}; border-radius: 15px;
        padding: 7px 14px; font-size: 12px;
    }}
    QPushButton#chip:hover {{ background-color: {p['panel2']}; border-color: {p['accent']}; }}
    QPushButton#link {{
        background: transparent; border: none; color: {p['accent']};
        padding: 4px 0; font-size: 12px;
    }}
    QPushButton#link:hover {{ color: {p['accent2']}; }}
    QPushButton#danger {{
        background: transparent; color: {p['danger']}; border: 1px solid {p['error_border']};
    }}
    QPushButton#danger:hover {{ background: {p['error_card']}; }}
    QPushButton#dialClose {{
        background: transparent; border: none; color: {p['muted']}; font-size: 14px;
    }}
    QPushButton#dialClose:hover {{ color: {p['text']}; background: {p['panel3']}; }}

    QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QDoubleSpinBox {{
        background-color: {p['bg']}; color: {p['text']};
        border: 1px solid {p['border2']}; border-radius: 9px;
        padding: {pad}px 11px; font-size: 12.5px;
        selection-background-color: {p['accent']};
        selection-color: {p['accent_text']};
    }}
    QPlainTextEdit#composer {{
        border-radius: 12px; padding: 11px 13px; font-size: 13px;
    }}
    QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus,
    QSpinBox:focus, QDoubleSpinBox:focus {{ border-color: {p['accent']}; }}

    QComboBox {{
        background-color: {p['panel3']}; color: {p['text']};
        border: 1px solid {p['border2']}; border-radius: 9px;
        padding: 6px 10px; font-size: 12px;
    }}
    QComboBox:hover {{ border-color: {p['accent']}; }}
    QComboBox::drop-down {{ border: none; width: 18px; }}
    QComboBox QAbstractItemView {{
        background-color: {p['panel2']}; color: {p['text']};
        border: 1px solid {p['border']}; selection-background-color: {p['accent_soft']};
        outline: none;
    }}

    QCheckBox, QRadioButton {{ spacing: 7px; color: {p['text']}; }}
    QCheckBox::indicator, QRadioButton::indicator {{
        width: 16px; height: 16px; border: 1px solid {p['border2']};
        border-radius: 4px; background: {p['panel3']};
    }}
    QCheckBox::indicator:checked {{
        background: {p['accent']}; border-color: {p['accent']};
        image: url("{check}");
    }}
    QRadioButton::indicator {{ border-radius: 8px; }}
    QRadioButton::indicator:checked {{
        background: {p['accent']}; border: 4px solid {p['panel']};
    }}

    QGroupBox {{
        border: 1px solid {p['border']}; border-radius: 10px;
        margin-top: 12px; padding: 12px 10px 8px 10px; font-weight: 600;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin; left: 12px; padding: 0 5px; color: {p['muted']};
    }}

    QTabWidget::pane {{
        border: 1px solid {p['border']}; border-radius: 10px;
        background: {p['panel']}; top: -1px;
    }}
    QTabBar::tab {{
        background: transparent; color: {p['muted']};
        border: none; padding: 8px 14px; margin-right: 3px;
        border-top-left-radius: 8px; border-top-right-radius: 8px;
    }}
    QTabBar::tab:hover {{ color: {p['text']}; background: {p['panel2']}; }}
    QTabBar::tab:selected {{
        color: {p['text']}; background: {p['panel']};
        border-bottom: 2px solid {p['accent']};
    }}

    QTableWidget, QTableView {{
        background: {p['bg']}; alternate-background-color: {p['panel2']};
        color: {p['text']}; border: 1px solid {p['border']};
        border-radius: 8px; gridline-color: {p['border']};
        selection-background-color: {p['accent_soft']};
        selection-color: {p['text']};
    }}
    QHeaderView::section {{
        background: {p['panel2']}; color: {p['muted']};
        border: none; border-right: 1px solid {p['border']};
        border-bottom: 1px solid {p['border']}; padding: 7px;
        font-size: 10.5px; font-weight: 700;
    }}
    QListWidget {{
        background: {p['bg']}; color: {p['text']};
        border: 1px solid {p['border']}; border-radius: 8px; outline: none;
    }}
    QListWidget::item {{ padding: 7px 8px; border-radius: 6px; }}
    QListWidget::item:selected {{ background: {p['accent_soft']}; color: {p['text']}; }}
    QListWidget::item:hover {{ background: {p['panel2']}; }}

    QSlider::groove:horizontal {{
        height: 4px; background: {p['panel3']}; border-radius: 2px;
    }}
    QSlider::sub-page:horizontal {{ background: {p['accent']}; border-radius: 2px; }}
    QSlider::handle:horizontal {{
        width: 14px; height: 14px; margin: -5px 0;
        background: {p['accent']}; border: 2px solid {p['panel']}; border-radius: 7px;
    }}
    QProgressBar {{
        background: {p['panel3']}; border: none; border-radius: 4px;
        height: 7px; text-align: center; color: transparent;
    }}
    QProgressBar::chunk {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {p['accent']}, stop:1 {p['accent2']});
        border-radius: 4px;
    }}

    QScrollBar:vertical {{ background: transparent; width: 10px; margin: 4px 2px 4px 0; }}
    QScrollBar::handle:vertical {{ background: {p['border2']}; border-radius: 4px; min-height: 30px; }}
    QScrollBar::handle:vertical:hover {{ background: {p['accent']}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
    QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 0 4px 2px 4px; }}
    QScrollBar::handle:horizontal {{ background: {p['border2']}; border-radius: 4px; min-width: 30px; }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

    QSplitter::handle {{ background: {p['border']}; width: 1px; }}
    QStatusBar {{ background: {p['panel']}; color: {p['muted']}; border-top: 1px solid {p['border']}; }}
    QToolTip {{
        background-color: {p['panel2']}; color: {p['text']};
        border: 1px solid {p['border2']}; padding: 5px 8px;
    }}
    """


def make_logo(size: int = 64, p: dict | None = None) -> QPixmap:
    """A rounded gradient tile with a stylised chat spark."""
    p = p or palette()
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)

    rect = QRectF(0.5, 0.5, size - 1, size - 1)
    path = QPainterPath()
    path.addRoundedRect(rect, size * 0.26, size * 0.26)
    grad = QLinearGradient(0, 0, size, size)
    grad.setColorAt(0, QColor(p["accent"]))
    grad.setColorAt(1, QColor(p["accent2"]))
    painter.fillPath(path, grad)

    # Soft highlight
    glow = QRadialGradient(QPointF(size * 0.28, size * 0.22), size * 0.7)
    glow.setColorAt(0, QColor(255, 255, 255, 70))
    glow.setColorAt(1, QColor(255, 255, 255, 0))
    painter.fillPath(path, glow)

    # Chat bubble glyph
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(255, 255, 255, 235))
    bw, bh = size * 0.48, size * 0.34
    bubble = QRectF((size - bw) / 2, size * 0.29, bw, bh)
    bpath = QPainterPath()
    bpath.addRoundedRect(bubble, bh * 0.34, bh * 0.34)
    tail = QPainterPath()
    tail.moveTo(size * 0.38, size * 0.58)
    tail.lineTo(size * 0.32, size * 0.68)
    tail.lineTo(size * 0.48, size * 0.6)
    tail.closeSubpath()
    painter.drawPath(bpath.united(tail))

    painter.setBrush(QColor(p["accent"]))
    dot = size * 0.055
    for i, fx in enumerate((0.4, 0.5, 0.6)):
        painter.drawEllipse(QPointF(size * fx, size * 0.46), dot, dot)
    painter.end()
    return pix


def make_app_icon(p: dict | None = None) -> QIcon:
    icon = QIcon()
    for size in (16, 24, 32, 48, 64, 128, 256):
        icon.addPixmap(make_logo(size, p))
    return icon


def make_splash_pixmap(p: dict | None = None, width: int = 560, height: int = 340,
                       version: str = APP_VERSION) -> QPixmap:
    """Painted splash artwork – no external assets required."""
    p = p or palette()
    pix = QPixmap(width, height)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)

    bg = QLinearGradient(0, 0, width, height)
    bg.setColorAt(0, QColor(p["bg"]))
    bg.setColorAt(0.55, QColor(p["panel"]))
    bg.setColorAt(1, QColor(p["bg"]))
    clip = QPainterPath()
    clip.addRoundedRect(QRectF(0, 0, width, height), 20, 20)
    painter.fillPath(clip, bg)

    # Ambient glows
    painter.setClipPath(clip)
    for cx, cy, radius, color, alpha in (
        (width * 0.13, height * 0.18, 180, p["accent"], 46),
        (width * 0.88, height * 0.8, 220, p["accent2"], 38),
    ):
        glow = QRadialGradient(QPointF(cx, cy), radius)
        c = QColor(color)
        c.setAlpha(alpha)
        glow.setColorAt(0, c)
        glow.setColorAt(1, QColor(color).darker(300))
        c2 = QColor(color)
        c2.setAlpha(0)
        glow.setColorAt(1, c2)
        painter.fillRect(0, 0, width, height, glow)

    # Dotted grid
    painter.setPen(QPen(QColor(p["border"]), 1))
    for x in range(30, width, 34):
        for y in range(24, height, 34):
            painter.setPen(QColor(255, 255, 255, 10 if p["bg"].startswith("#0") else 40))
            painter.drawPoint(x, y)

    logo_size = 78
    logo = make_logo(logo_size, p)
    painter.drawPixmap(int((width - logo_size) / 2), 54, logo)

    painter.setPen(QColor(p["text"]))
    font = QFont("Segoe UI", 24, QFont.Bold)
    painter.setFont(font)
    painter.drawText(QRectF(0, 148, width, 40), Qt.AlignCenter, "GroqChatbot")

    painter.setPen(QColor(p["muted"]))
    painter.setFont(QFont("Segoe UI", 10))
    painter.drawText(QRectF(0, 188, width, 24), Qt.AlignCenter,
                     "AI agent with memory, tools, RAG and a creation studio")

    # Feature chips
    chips = ["⚡ Groq LPU", "🧠 Memory", "📚 RAG", "🛠 Tools", "🎨 Generate"]
    chip_font = QFont("Segoe UI", 8)
    painter.setFont(chip_font)
    widths = [painter.fontMetrics().horizontalAdvance(c) + 20 for c in chips]
    total = sum(widths) + 8 * (len(chips) - 1)
    x = (width - total) / 2
    for chip, w in zip(chips, widths):
        r = QRectF(x, 226, w, 26)
        painter.setPen(QPen(QColor(p["border2"]), 1))
        painter.setBrush(QColor(p["panel2"]))
        painter.drawRoundedRect(r, 13, 13)
        painter.setPen(QColor(p["muted"]))
        painter.drawText(r, Qt.AlignCenter, chip)
        x += w + 8

    # Progress shimmer
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(p["panel3"]))
    painter.drawRoundedRect(QRectF(90, height - 48, width - 180, 6), 3, 3)
    shimmer = QLinearGradient(90, 0, width - 90, 0)
    shimmer.setColorAt(0, QColor(p["accent"]))
    shimmer.setColorAt(0.6, QColor(p["accent2"]))
    shimmer.setColorAt(1, QColor(p["accent"]))
    painter.setBrush(shimmer)
    painter.drawRoundedRect(QRectF(90, height - 48, (width - 180) * 0.62, 6), 3, 3)

    painter.setPen(QColor(p["faint"]))
    painter.setFont(QFont("Segoe UI", 8))
    painter.drawText(QRectF(90, height - 32, width - 180, 20), Qt.AlignLeft, f"v{version}")
    painter.drawText(QRectF(90, height - 32, width - 180, 20), Qt.AlignRight,
                     "Starting local systems…")
    painter.end()
    return pix


def save_icon_files(directory: str = ".") -> list[str]:
    """Write PNG + ICO app icons next to the application (used by PyInstaller)."""
    os.makedirs(directory, exist_ok=True)
    png_path = os.path.join(directory, "app_icon.png")
    ico_path = os.path.join(directory, "app_icon.ico")
    pix = make_logo(256)
    pix.save(png_path, "PNG")

    # ICO containers accept a PNG payload directly (Vista+).
    try:
        with open(png_path, "rb") as handle:
            png = handle.read()
        header = bytearray()
        header += b"\x00\x00\x01\x00\x01\x00"
        header += bytes([0, 0])              # width 256
        header += bytes([0, 0])              # height 256
        header += bytes([0, 0, 0, 0])        # palette, reserved
        header += (1).to_bytes(2, "little")  # planes
        header += (32).to_bytes(2, "little") # bpp
        header += len(png).to_bytes(4, "little")
        header += (22).to_bytes(4, "little") # offset
        with open(ico_path, "wb") as handle:
            handle.write(bytes(header) + png)
    except OSError:
        pass
    return [png_path, ico_path]
