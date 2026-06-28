"""
Task history dashboard — a secondary panel showing recent task results.
Toggled with Cmd+Ctrl+D. Shows task description, success/failure, step count, duration.
"""
from __future__ import annotations

import logging
from typing import Any

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

log = logging.getLogger(__name__)

BG_COLOR = "#141414"
CARD_COLOR = "#1e1e1e"
BORDER_COLOR = "#2a2a2a"
TEXT_COLOR = "#e0e0e0"
HINT_COLOR = "#555555"
SUCCESS_COLOR = "#22c55e"
FAILURE_COLOR = "#ef4444"
ACCENT_COLOR = "#06b6d4"

DASHBOARD_WIDTH = 400
DASHBOARD_HEIGHT = 600


class TaskCard(QFrame):
    def __init__(self, task: dict[str, Any]) -> None:
        super().__init__()
        self.setStyleSheet(
            f"QFrame {{ background: {CARD_COLOR}; border: 1px solid {BORDER_COLOR}; "
            f"border-radius: 8px; margin: 2px 0; }}"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        # Top row: description + status dot
        top = QHBoxLayout()

        desc = QLabel(task.get("description", "")[:80])
        desc.setFont(QFont("SF Pro Text", 13))
        desc.setStyleSheet(f"color: {TEXT_COLOR}; border: none; background: transparent;")
        desc.setWordWrap(True)
        top.addWidget(desc, 1)

        success = task.get("success")
        dot_color = SUCCESS_COLOR if success else (FAILURE_COLOR if success is False else HINT_COLOR)
        dot = QLabel("●")
        dot.setFont(QFont("SF Pro Text", 12))
        dot.setStyleSheet(f"color: {dot_color}; border: none; background: transparent;")
        dot.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        top.addWidget(dot)
        layout.addLayout(top)

        # Bottom row: step count + duration + timestamp
        meta_parts = []
        if task.get("steps_total"):
            meta_parts.append(f"{task['steps_completed']}/{task['steps_total']} steps")
        if task.get("duration_ms"):
            meta_parts.append(f"{task['duration_ms']/1000:.1f}s")
        if task.get("created_at"):
            ts = task["created_at"][:16].replace("T", " ")
            meta_parts.append(ts)

        if meta_parts:
            meta = QLabel(" · ".join(meta_parts))
            meta.setFont(QFont("SF Pro Text", 11))
            meta.setStyleSheet(f"color: {HINT_COLOR}; border: none; background: transparent;")
            layout.addWidget(meta)


class Dashboard(QWidget):
    """Floating panel showing recent task history. Refreshes every 5s when visible."""

    def __init__(self, memory) -> None:
        super().__init__()
        self._memory = memory
        self._setup_ui()
        self._refresh_timer = QTimer()
        self._refresh_timer.setInterval(5000)
        self._refresh_timer.timeout.connect(self._refresh)

    def _setup_ui(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(DASHBOARD_WIDTH, DASHBOARD_HEIGHT)
        self.setStyleSheet(
            f"QWidget {{ background: {BG_COLOR}; border: 1px solid {BORDER_COLOR}; "
            f"border-radius: 12px; }}"
        )

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(8)

        title = QLabel("Recent Tasks")
        title.setFont(QFont("SF Pro Display", 15, QFont.Weight.SemiBold))
        title.setStyleSheet(f"color: {TEXT_COLOR}; background: transparent; border: none;")
        outer.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._cards_container = QWidget()
        self._cards_container.setStyleSheet("background: transparent;")
        self._cards_layout = QVBoxLayout(self._cards_container)
        self._cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._cards_layout.setSpacing(6)

        scroll.setWidget(self._cards_container)
        outer.addWidget(scroll)

    def show(self) -> None:
        super().show()
        self._refresh()
        self._refresh_timer.start()

    def hide(self) -> None:
        super().hide()
        self._refresh_timer.stop()

    def _refresh(self) -> None:
        # Clear existing cards
        while self._cards_layout.count():
            item = self._cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        tasks = self._memory.recent_tasks(20)
        if not tasks:
            placeholder = QLabel("No tasks yet. Press Cmd+Ctrl+Space to start.")
            placeholder.setFont(QFont("SF Pro Text", 13))
            placeholder.setStyleSheet(f"color: {HINT_COLOR}; background: transparent; border: none;")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._cards_layout.addWidget(placeholder)
        else:
            for task in tasks:
                self._cards_layout.addWidget(TaskCard(task))
