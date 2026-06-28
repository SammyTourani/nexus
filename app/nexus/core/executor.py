"""
Action executor: translates ActionSteps into real macOS UI interactions.
Strategy: AX tree first (fast), vision fallback (when AX empty), then pyautogui.
"""
from __future__ import annotations

import logging
import subprocess
import time
from dataclasses import dataclass
from typing import Optional

import pyautogui

from nexus.core.ax_tree import AXTreeWalker, AXElement
from nexus.core.planner import ActionStep
from nexus.core.verifier import Verifier, VerificationResult
from nexus.core.vision import VisionEngine

log = logging.getLogger(__name__)

pyautogui.PAUSE = 0.1
pyautogui.FAILSAFE = True

MAX_RETRIES = int(__import__("os").getenv("NEXUS_MAX_RETRIES", "3"))


@dataclass
class StepResult:
    step: ActionStep
    success: bool
    method: str
    reason: str
    duration_ms: float


class Executor:
    """
    Executes a plan step by step.
    Each step is attempted via AX tree first, then vision fallback.
    After each step, the verifier confirms success before proceeding.
    """

    def __init__(self, ax: AXTreeWalker, vision: VisionEngine, verifier: Verifier) -> None:
        self._ax = ax
        self._vision = vision
        self._verifier = verifier

    def execute_plan(
        self,
        steps: list[ActionStep],
        task_description: str,
        on_step_complete: Optional[callable] = None,
    ) -> list[StepResult]:
        """
        Execute all steps in sequence.
        Returns results for all steps, including failed ones.
        Stops on unrecoverable failure.
        """
        results: list[StepResult] = []

        for i, step in enumerate(steps):
            log.info("Step %d/%d: %s '%s'", i + 1, len(steps), step.action, step.target)

            result = self._execute_step_with_retry(step)
            results.append(result)

            if on_step_complete:
                on_step_complete(i + 1, len(steps), result)

            if not result.success:
                log.warning("Step %d failed after retries: %s", i + 1, result.reason)
                break

            time.sleep(0.3)

        return results

    def _execute_step_with_retry(self, step: ActionStep) -> StepResult:
        for attempt in range(MAX_RETRIES):
            if attempt > 0:
                time.sleep(0.5 * attempt)
                log.debug("Retry %d/%d for step: %s", attempt + 1, MAX_RETRIES, step)

            result = self._execute_step(step)
            if result.success:
                return result

        return result  # return last failure

    def _execute_step(self, step: ActionStep) -> StepResult:
        t0 = time.perf_counter()
        method = "unknown"
        success = False
        reason = ""

        try:
            if step.action == "click":
                method, success, reason = self._click(step.target)

            elif step.action == "type":
                text = step.params.get("text", "")
                pyautogui.write(text, interval=0.03)
                method = "pyautogui"
                success = True
                reason = f"Typed {len(text)} characters"

            elif step.action == "hotkey":
                keys = step.params.get("keys", [])
                pyautogui.hotkey(*keys)
                method = "pyautogui"
                time.sleep(0.2)
                success = True
                reason = f"Pressed {'+'.join(keys)}"

            elif step.action == "scroll":
                direction = step.params.get("direction", "down")
                amount = int(step.params.get("amount", 3))
                clicks = amount if direction == "down" else -amount
                pyautogui.scroll(clicks)
                method = "pyautogui"
                success = True
                reason = f"Scrolled {direction} {amount}"

            elif step.action == "focus_app":
                success, reason = self._focus_app(step.target)
                method = "applescript"

            elif step.action == "wait":
                time.sleep(1.5)
                method = "sleep"
                success = True
                reason = "Waited 1.5s"

            elif step.action == "screenshot":
                method = "capture"
                success = True
                reason = "Screenshot captured for context"

            else:
                reason = f"Unknown action type: {step.action}"
                success = False

        except Exception as e:
            reason = str(e)
            success = False
            log.error("Step execution error: %s", e)

        elapsed_ms = (time.perf_counter() - t0) * 1000

        if success and step.action not in ("wait", "screenshot", "scroll"):
            verification = self._verify_step(step)
            if not verification.success:
                success = False
                reason = f"Executed but verification failed: {verification.reason}"
                log.warning("Verification failed for step %s: %s", step, verification.reason)

        return StepResult(
            step=step,
            success=success,
            method=method,
            reason=reason,
            duration_ms=elapsed_ms,
        )

    def _click(self, target: str) -> tuple[str, bool, str]:
        """Try AX tree click, fall back to vision if tree is empty."""
        el = self._ax.find(target)
        if el and el.enabled:
            pyautogui.click(el.cx, el.cy)
            log.debug("AX click: '%s' at (%.0f, %.0f)", target, el.cx, el.cy)
            return "ax_tree", True, f"Clicked '{el.label}' via AX at ({el.cx:.0f},{el.cy:.0f})"

        # AX miss — fall back to vision
        log.debug("AX miss for '%s', trying vision fallback", target)
        vr = self._vision.find_element(target)
        if vr:
            pyautogui.click(vr.x, vr.y)
            log.debug("Vision click: '%s' at (%.0f, %.0f)", target, vr.x, vr.y)
            return "vision", True, f"Clicked '{target}' via vision at ({vr.x:.0f},{vr.y:.0f})"

        return "none", False, f"Could not locate element: '{target}' via AX or vision"

    def _focus_app(self, app_name: str) -> tuple[bool, str]:
        script = f'tell application "{app_name}" to activate'
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            time.sleep(0.5)
            return True, f"Activated {app_name}"
        return False, f"Failed to activate {app_name}: {result.stderr.strip()}"

    def _verify_step(self, step: ActionStep) -> VerificationResult:
        descriptions = {
            "click": f"clicked '{step.target}'",
            "type": f"typed text into the active field",
            "hotkey": f"pressed {'+'.join(step.params.get('keys', []))}",
            "focus_app": f"switched to {step.target}",
        }
        action_desc = descriptions.get(step.action, f"executed {step.action}")

        expected = {
            "click": f"The UI responded to clicking '{step.target}' — either the element is now selected, a new view appeared, or a dialog opened.",
            "type": "The typed text appears in the active input field.",
            "hotkey": "The keyboard shortcut triggered its expected effect.",
            "focus_app": f"{step.target} is now the frontmost window.",
        }.get(step.action, "The action had a visible effect on the screen.")

        return self._verifier.verify(action_desc, expected)
