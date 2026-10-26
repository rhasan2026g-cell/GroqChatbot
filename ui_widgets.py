"""Small reusable widgets: stat cards, badges and a tiny activity chart."""

from __future__ import annotations

from datetime import datetime, timedelta

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget


class StatCard(QFrame):
    """Compact metric tile used by the sidebar and the database view."""

    def __init__(self, title: str, value: str = "0", hint: str = "", icon: str = "",
                 accent: str = "#4c8dff", parent=None):
        super().__init__(parent)
        self.setObjectName("statCard")
        self.setStyleSheet(
            f"QFrame#statCard {{ background: rgba(255,255,255,0.025);"
            f" border: 1px solid rgba(255,255,255,0.07); border-radius: 10px; }}"
        )
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        outer = QHBoxLayout(self)
        outer.setContentsMargins(10, 8, 10, 8)
        outer.setSpacing(9)

        self.icon_label = QLabel(icon)
        self.icon_label.setFixedSize(28, 28)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setStyleSheet(
            f"background: {accent}22; color: {accent}; border-radius: 8px; font-size: 14px;"
        )
        outer.addWidget(self.icon_label)

        text = QVBoxLayout()
        text.setSpacing(0)
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color:#7c8aa0; font-size:9.5px; font-weight:600;")
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("color:#e6edf8; font-size:15px; font-weight:700;")
        text.addWidget(self.title_label)
        text.addWidget(self.value_label)
        outer.addLayout(text, 1)

        self.hint_label = QLabel(hint)
        self.hint_label.setStyleSheet(f"color:{accent}; font-size:9px;")
        self.hint_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        outer.addWidget(self.hint_label)

    def set_value(self, value: str, hint: str | None = None) -> None:
        self.value_label.setText(str(value))
        if hint is not None:
            self.hint_label.setText(hint)

    def set_theme(self, text: str, muted: str, accent: str, card_bg: str = "rgba(255,255,255,0.025)",
                  card_border: str = "rgba(255,255,255,0.07)") -> None:
        self.setStyleSheet(
            f"QFrame#statCard {{ background: {card_bg};"
            f" border: 1px solid {card_border}; border-radius: 10px; }}"
        )
        self.title_label.setStyleSheet(f"color:{muted}; font-size:9.5px; font-weight:600;")
        self.value_label.setStyleSheet(f"color:{text}; font-size:15px; font-weight:700;")
        self.icon_label.setStyleSheet(
            f"background:{accent}22; color:{accent}; border-radius:8px; font-size:14px;"
        )
        self.hint_label.setStyleSheet(f"color:{accent}; font-size:9px;")


class Badge(QLabel):
    """Tiny coloured status pill."""

    def __init__(self, text: str = "", kind: str = "muted", parent=None):
        super().__init__(text, parent)
        self.setObjectName("badge")
        self.setAlignment(Qt.AlignCenter)
        self.set_kind(kind)

    def set_kind(self, kind: str) -> None:
        colors = {
            "ok": ("#34d399", "rgba(52,211,153,0.12)"),
            "warn": ("#fbbf24", "rgba(251,191,36,0.12)"),
            "bad": ("#f87171", "rgba(248,113,113,0.12)"),
            "accent": ("#4c8dff", "rgba(76,141,255,0.14)"),
            "muted": ("#8a98ad", "rgba(138,152,173,0.10)"),
        }
        fg, bg = colors.get(kind, colors["muted"])
        self.setStyleSheet(
            f"QLabel#badge {{ color:{fg}; background:{bg}; border:1px solid {fg}44;"
            f" border-radius:8px; padding:1px 7px; font-size:9.5px; font-weight:600; }}"
        )


class MiniChart(QWidget):
    """A dependency-free bar chart for recent memory activity."""

    DAYS = ("M", "T", "W", "T", "F", "S", "S")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(66)
        self.setMaximumHeight(78)
        self.values: list[float] = []
        self.labels: list[str] = list("MTWTFSS")
        self.accent = "#4c8dff"
        self.accent2 = "#8b5cf6"
        self.muted = "#243047"
        self.text = "#e6edf8"

    def set_values(self, values: list[float], accent: str = "#4c8dff",
                   accent2: str = "#8b5cf6", muted: str = "#243047",
                   text: str = "#e6edf8") -> None:
        self.values = list(values)
        self.accent = accent
        self.accent2 = accent2
        self.muted = muted
        self.text = text
        today = datetime.now().date()
        count = len(self.values) or 7
        self.labels = [
            "MTWTFSS"[(today - timedelta(days=(count - 1 - index))).weekday()]
            for index in range(count)
        ]
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt signature
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        label_height = 13
        rect = QRectF(
            self.rect().left(), self.rect().top() + 3,
            self.rect().width(), self.rect().height() - label_height - 4,
        )
        font = QFont(self.font())
        font.setPointSizeF(max(6.5, font.pointSizeF() - 2.4))
        painter.setFont(font)

        if not self.values or sum(self.values) <= 0:
            painter.setPen(QColor(self.muted))
            painter.drawText(rect, Qt.AlignCenter, "No activity in the last 7 days")
            painter.end()
            return

        count = len(self.values)
        slot = rect.width() / max(count, 1)
        bar_width = max(4.0, min(24.0, slot - 8))
        peak = max(self.values) or 1
        grad = QLinearGradient(0, rect.top(), 0, rect.bottom())
        grad.setColorAt(0, QColor(self.accent2))
        grad.setColorAt(1, QColor(self.accent))
        baseline = rect.bottom()

        axis = QColor(self.muted)
        axis.setAlpha(150)
        painter.setPen(QPen(axis, 1))
        painter.drawLine(int(rect.left()), int(baseline) + 1,
                         int(rect.right()), int(baseline) + 1)

        def bar_x(index: int) -> float:
            return rect.left() + index * slot + (slot - bar_width) / 2

        for index, value in enumerate(self.values):
            if value <= 0:
                continue
            height = max(6.0, (value / peak) * (rect.height() - 3))
            bar = QRectF(bar_x(index), baseline - height, bar_width, height)
            path = QPainterPath()
            path.addRoundedRect(bar, min(3, bar_width / 2), min(3, bar_width / 2))
            painter.setPen(Qt.NoPen)
            painter.setBrush(grad)
            painter.drawPath(path)

        for index in range(count):
            x = bar_x(index)
            is_today = index == count - 1
            if is_today:
                bold = QFont(self.font())
                bold.setPointSizeF(max(6.5, self.font().pointSizeF() - 2.0))
                bold.setBold(True)
                painter.setFont(bold)
            painter.setPen(QColor(self.accent if is_today else self.muted))
            label = self.labels[index] if index < len(self.labels) else "·"
            painter.drawText(
                QRectF(x, baseline + 2, bar_width, label_height),
                Qt.AlignHCenter | Qt.AlignTop,
                label,
            )
            if is_today:
                painter.setFont(font)
        painter.end()
