"""
NEXUS entry point.
Registers the global hotkey (Cmd+Ctrl+Space), starts the Qt app,
wires up all core modules, and provides the task runner to the UI.
"""
from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass
from typing import Callable, Optional

from dotenv import load_dotenv
from pynput import keyboard
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QThread, pyqtSignal, QObject

load_dotenv()

log = logging.getLogger(__name__)
logging.basicConfig(
    level=getattr(logging, os.getenv("NEXUS_LOG_LEVEL", "INFO")),
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)


@dataclass
class TaskResult:
    success: bool
    summary: str
    steps_completed: int
    steps_total: int


class HotkeySignal(QObject):
    triggered = pyqtSignal()


class NexusApp:
    """
    Top-level orchestrator. Owns all modules and wires them together.
    Designed to run as a macOS menu bar / background app (LSUIElement = true).
    """

    def __init__(self) -> None:
        self._qt_app = QApplication(sys.argv)
        self._qt_app.setQuitOnLastWindowClosed(False)
        self._hotkey_signal = HotkeySignal()
        self._setup_modules()
        self._setup_ui()
        self._setup_hotkey()
        self._setup_tray()

    def _setup_modules(self) -> None:
        from nexus.core.ax_tree import AXTreeWalker
        from nexus.core.vision import VisionEngine
        from nexus.core.planner import Planner
        from nexus.core.verifier import Verifier
        from nexus.core.executor import Executor
        from nexus.core.memory import Memory

        try:
            self._ax = AXTreeWalker()
        except PermissionError as e:
            log.error("Accessibility permission denied: %s", e)
            self._show_permission_alert("Accessibility")
            sys.exit(1)

        self._vision = VisionEngine()
        self._planner = Planner()
        self._verifier = Verifier()
        self._executor = Executor(self._ax, self._vision, self._verifier)
        self._memory = Memory()

    def _setup_ui(self) -> None:
        from nexus.ui.spotlight import SpotlightWindow
        from nexus.ui.dashboard import Dashboard

        self._spotlight = SpotlightWindow(task_runner=self._run_task)
        self._dashboard = Dashboard(memory=self._memory)
        self._hotkey_signal.triggered.connect(self._spotlight.show_window)

    def _setup_hotkey(self) -> None:
        def on_activate():
            self._hotkey_signal.triggered.emit()

        hotkey = keyboard.GlobalHotKeys({
            "<ctrl>+<cmd>+space": on_activate,
        })
        hotkey.daemon = True
        hotkey.start()
        log.info("Global hotkey registered: Cmd+Ctrl+Space")

    def _setup_tray(self) -> None:
        tray = QSystemTrayIcon(self._qt_app)
        icon = QIcon.fromTheme("application")
        tray.setIcon(icon)
        tray.setToolTip("NEXUS — AI automation agent")

        menu = QMenu()
        show_action = menu.addAction("Open NEXUS")
        show_action.triggered.connect(self._spotlight.show_window)
        history_action = menu.addAction("Task History")
        history_action.triggered.connect(self._dashboard.show)
        menu.addSeparator()
        quit_action = menu.addAction("Quit NEXUS")
        quit_action.triggered.connect(self._qt_app.quit)

        tray.setContextMenu(menu)
        tray.setVisible(True)

    def _run_task(
        self,
        task: str,
        on_progress: Optional[Callable[[int, int, str], None]] = None,
    ) -> TaskResult:
        """
        Full task execution pipeline:
        1. Check memory cache
        2. Build screen description
        3. Plan (Claude Sonnet 4.6)
        4. Execute step by step (AX → vision → pyautogui)
        5. Verify (Claude Haiku 4.5 after each step)
        6. Cache on success
        """
        import time
        t0 = time.perf_counter()

        task_id = self._memory.start_task(task)

        # Step 1: Check cache
        cached = self._memory.get_cached_steps(task)
        memory_hint = ""
        if cached:
            log.info("Cache hit — using %d cached steps as hint", len(cached))
            import json
            memory_hint = json.dumps(cached)

        # Step 2: Describe current screen
        if on_progress:
            on_progress(0, 1, "Reading screen...")
        screen_desc = ""
        try:
            ax_elements = self._ax.walk()
            if ax_elements:
                labels = [el.label for el in ax_elements[:15]]
                screen_desc = f"Visible elements: {', '.join(labels)}"
            else:
                screen_desc = self._vision.describe_screen()
        except Exception as e:
            log.warning("Screen description failed: %s", e)

        # Step 3: Plan
        if on_progress:
            on_progress(0, 1, "Planning...")
        plan = self._planner.plan(task, screen_desc, memory_hint)
        log.info("Plan: %d steps — %s", len(plan), plan.task_summary)

        # Step 4 & 5: Execute with verification
        def _on_step(current: int, total: int, result) -> None:
            if on_progress:
                on_progress(current, total, f"{result.step.action} '{result.step.target}'")

        step_results = self._executor.execute_plan(
            plan.steps,
            task_description=task,
            on_step_complete=_on_step,
        )

        # Step 6: Final verification + cache
        completed = sum(1 for r in step_results if r.success)
        total = len(step_results)
        overall_success = completed == total

        if overall_success:
            steps_for_cache = [
                {"action": r.step.action, "target": r.step.target, "params": r.step.params}
                for r in step_results
            ]
            self._memory.cache_steps(task, steps_for_cache)
            log.info("Cached %d steps for future runs", len(steps_for_cache))

        duration_ms = (time.perf_counter() - t0) * 1000
        self._memory.complete_task(
            task_id,
            success=overall_success,
            steps_total=total,
            steps_completed=completed,
            duration_ms=duration_ms,
        )

        if overall_success:
            summary = f"Done in {duration_ms/1000:.1f}s ({total} steps)"
        else:
            failed_step = next((r for r in step_results if not r.success), None)
            reason = failed_step.reason if failed_step else "Unknown error"
            summary = f"Failed at step {completed + 1}/{total}: {reason}"

        return TaskResult(
            success=overall_success,
            summary=summary,
            steps_completed=completed,
            steps_total=total,
        )

    def _show_permission_alert(self, permission_type: str) -> None:
        from PyQt6.QtWidgets import QMessageBox
        msg = QMessageBox()
        msg.setWindowTitle("Permission Required")
        msg.setText(
            f"NEXUS needs {permission_type} permission to run.\n\n"
            f"Open System Settings > Privacy & Security > {permission_type} "
            f"and enable NEXUS, then restart."
        )
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

    def run(self) -> int:
        log.info("NEXUS started. Press Cmd+Ctrl+Space to open.")
        return self._qt_app.exec()


def main() -> None:
    app = NexusApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
