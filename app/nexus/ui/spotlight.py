"""
Spotlight-style command window — the main user interface for NEXUS.
Opens with Cmd+Ctrl+Space. Frameless, centered, dismisses on Escape.
Emits a task_submitted signal when the user presses Enter.
"""
from __future__ import annotations

import logging

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QFont, QKeySequence, QPainter, QPainterPath, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QLabel,
    QLineEdit,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

log = logging.getLogger(__name__)

WINDOW_WIDTH = 680
WINDOW_HEIGHT_IDLE = 72
WINDOW_HEIGHT_ACTIVE = 200
CORNER_RADIUS = 14
BG_COLOR = "#1a1a1a"
BORDER_COLOR = "#3a3a3a"
ACCENT_COLOR = "#06b6d4"
TEXT_COLOR = "#f0f0f0"
HINT_COLOR = "#555555"


class TaskWorker(QThread):
    """Runs the NEXUS execution pipeline off the main thread."""
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(bool, str)

    def __init__(self, task: str, runner) -> None:
        super().__init__()
        self._task = task
        self._runner = runner

    def run(self) -> None:
        try:
            result = self._runner(
                self._task,
                on_progress=lambda current, total, msg: self.progress.emit(current, total, msg),
            )
            self.finished.emit(result.success, result.summary)
        except Exception as e:
            self.finished.emit(False, str(e))


class SpotlightWindow(QWidget):
    """
    Floating, frameless command bar.
    Shows task input → progress → result in a single compact window.
    """
    task_submitted = pyqtSignal(str)

    def __init__(self, task_runner=None) -> None:
        super().__init__()
        self._task_runner = task_runner
        self._worker: TaskWorker | None = None
        self._is_active = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(WINDOW_WIDTH)
        self.setFixedHeight(WINDOW_HEIGHT_IDLE)

        self._outer = QFrame(self)
        self._outer.setGeometry(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT_IDLE)
        self._outer.setStyleSheet(
            f"QFrame {{ background-color: {BG_COLOR}; "
            f"border: 1px solid {BORDER_COLOR}; "
            f"border-radius: {CORNER_RADIUS}px; }}"
        )

        layout = QVBoxLayout(self._outer)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(4)

        # Command input
        self._input = QLineEdit()
        self._input.setPlaceholderText("What do you want to do?")
        self._input.setFont(QFont("SF Pro Display", 17))
        self._input.setStyleSheet(
            f"QLineEdit {{ background: transparent; border: none; "
            f"color: {TEXT_COLOR}; padding: 4px 0; }}"
            f"QLineEdit::placeholder {{ color: {HINT_COLOR}; }}"
        )
        self._input.setFixedHeight(52)
        self._input.returnPressed.connect(self._on_submit)
        layout.addWidget(self._input)

        # Status label (hidden when idle)
        self._status_label = QLabel("")
        self._status_label.setFont(QFont("SF Pro Text", 13))
        self._status_label.setStyleSheet(f"color: {HINT_COLOR}; background: transparent; border: none;")
        self._status_label.setVisible(False)
        layout.addWidget(self._status_label)

        # Progress bar (hidden when idle)
        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setFixedHeight(3)
        self._progress.setStyleSheet(
            f"QProgressBar {{ background: {BORDER_COLOR}; border-radius: 1px; border: none; }}"
            f"QProgressBar::chunk {{ background: {ACCENT_COLOR}; border-radius: 1px; }}"
        )
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        # Result label
        self._result_label = QLabel("")
        self._result_label.setFont(QFont("SF Pro Text", 13))
        self._result_label.setWordWrap(True)
        self._result_label.setStyleSheet(f"color: {TEXT_COLOR}; background: transparent; border: none;")
        self._result_label.setVisible(False)
        layout.addWidget(self._result_label)

        # Keyboard shortcuts
        QShortcut(QKeySequence("Escape"), self, self.hide_window)
        QShortcut(QKeySequence("Ctrl+L"), self, self._input.clear)

        self._center_on_screen()

    def _center_on_screen(self) -> None:
        screen = QApplication.primaryScreen()
        if screen:
            rect = screen.geometry()
            x = (rect.width() - WINDOW_WIDTH) // 2
            y = rect.height() // 3
            self.move(x, y)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), CORNER_RADIUS, CORNER_RADIUS)
        painter.setClipPath(path)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))

    def show_window(self) -> None:
        self._center_on_screen()
        self._reset_state()
        self.show()
        self.raise_()
        self.activateWindow()
        self._input.setFocus()

    def hide_window(self) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.terminate()
        self.hide()

    def _reset_state(self) -> None:
        self._input.clear()
        self._input.setEnabled(True)
        self._status_label.setVisible(False)
        self._progress.setVisible(False)
        self._result_label.setVisible(False)
        self._is_active = False
        self.setFixedHeight(WINDOW_HEIGHT_IDLE)
        self._outer.setGeometry(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT_IDLE)

    def _set_active_state(self) -> None:
        self._is_active = True
        self._input.setEnabled(False)
        self._status_label.setVisible(True)
        self._progress.setVisible(True)
        self.setFixedHeight(WINDOW_HEIGHT_ACTIVE)
        self._outer.setGeometry(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT_ACTIVE)
        self._center_on_screen()

    def _on_submit(self) -> None:
        task = self._input.text().strip()
        if not task or not self._task_runner:
            return

        self._set_active_state()
        self._status_label.setText("Planning...")
        self._progress.setValue(5)

        self._worker = TaskWorker(task, self._task_runner)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _on_progress(self, current: int, total: int, message: str) -> None:
        pct = int((current / max(total, 1)) * 90) + 5
        self._progress.setValue(pct)
        self._status_label.setText(f"Step {current}/{total}: {message}")

    def _on_finished(self, success: bool, summary: str) -> None:
        self._progress.setValue(100)
        color = ACCENT_COLOR if success else "#ef4444"
        icon = "Done" if success else "Failed"
        self._status_label.setText(f"{icon}")
        self._status_label.setStyleSheet(f"color: {color}; background: transparent; border: none;")
        self._result_label.setText(summary)
        self._result_label.setVisible(True)

        # Auto-close after 3s on success, stay open on failure
        if success:
            QTimer.singleShot(3000, self.hide_window)
