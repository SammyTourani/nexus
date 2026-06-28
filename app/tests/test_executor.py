"""
Tests for the action executor module.
All external dependencies (AX tree, vision, verifier, pyautogui) are mocked.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from nexus.core.executor import Executor, StepResult
from nexus.core.planner import ActionStep, Plan


@pytest.fixture
def executor(mock_ax_walker, mock_vision, mock_verifier_success):
    return Executor(
        ax=mock_ax_walker,
        vision=mock_vision,
        verifier=mock_verifier_success,
    )


class TestClickAction:
    def test_click_via_ax_tree(self, executor, mock_ax_walker):
        step = ActionStep(action="click", target="Submit", params={})
        with patch("nexus.core.executor.pyautogui.click") as mock_click:
            result = executor._execute_step(step)
        assert result.success
        assert result.method == "ax_tree"
        mock_click.assert_called_once()

    def test_click_falls_back_to_vision_when_ax_empty(self, mock_ax_walker, mock_vision, mock_verifier_success):
        mock_ax_walker.find.return_value = None
        ex = Executor(ax=mock_ax_walker, vision=mock_vision, verifier=mock_verifier_success)
        step = ActionStep(action="click", target="NonExistentButton", params={})
        with patch("nexus.core.executor.pyautogui.click"):
            result = ex._execute_step(step)
        assert result.method == "vision"
        assert result.success

    def test_click_fails_when_both_ax_and_vision_miss(self, mock_verifier_success):
        ax = MagicMock()
        ax.find.return_value = None
        vision = MagicMock()
        vision.find_element.return_value = None
        ex = Executor(ax=ax, vision=vision, verifier=mock_verifier_success)

        step = ActionStep(action="click", target="GhostButton", params={})
        result = ex._execute_step(step)

        assert not result.success
        assert result.method == "none"
        assert "GhostButton" in result.reason


class TestTypeAction:
    def test_type_action_calls_pyautogui_write(self, executor):
        step = ActionStep(action="type", target="", params={"text": "hello world"})
        with patch("nexus.core.executor.pyautogui.write") as mock_write:
            result = executor._execute_step(step)
        assert result.success
        mock_write.assert_called_once_with("hello world", interval=0.03)

    def test_type_with_empty_text_still_succeeds(self, executor):
        step = ActionStep(action="type", target="", params={"text": ""})
        with patch("nexus.core.executor.pyautogui.write"):
            result = executor._execute_step(step)
        assert result.success


class TestHotkeyAction:
    def test_hotkey_cmd_t(self, executor):
        step = ActionStep(action="hotkey", target="", params={"keys": ["cmd", "t"]})
        with patch("nexus.core.executor.pyautogui.hotkey") as mock_hotkey:
            result = executor._execute_step(step)
        assert result.success
        mock_hotkey.assert_called_once_with("cmd", "t")

    def test_hotkey_escape(self, executor):
        step = ActionStep(action="hotkey", target="", params={"keys": ["escape"]})
        with patch("nexus.core.executor.pyautogui.hotkey") as mock_hotkey:
            result = executor._execute_step(step)
        assert result.success
        mock_hotkey.assert_called_with("escape")


class TestScrollAction:
    def test_scroll_down(self, executor):
        step = ActionStep(action="scroll", target="", params={"direction": "down", "amount": 3})
        with patch("nexus.core.executor.pyautogui.scroll") as mock_scroll:
            result = executor._execute_step(step)
        assert result.success
        mock_scroll.assert_called_once_with(3)

    def test_scroll_up_is_negative(self, executor):
        step = ActionStep(action="scroll", target="", params={"direction": "up", "amount": 5})
        with patch("nexus.core.executor.pyautogui.scroll") as mock_scroll:
            result = executor._execute_step(step)
        assert result.success
        mock_scroll.assert_called_once_with(-5)


class TestFocusApp:
    def test_focus_safari(self, executor):
        step = ActionStep(action="focus_app", target="Safari", params={})
        with patch("nexus.core.executor.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            result = executor._execute_step(step)
        assert result.success
        assert "Safari" in result.reason

    def test_focus_nonexistent_app_fails(self, executor):
        step = ActionStep(action="focus_app", target="NonExistentApp999", params={})
        with patch("nexus.core.executor.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr="app not found")
            result = executor._execute_step(step)
        assert not result.success


class TestExecutePlan:
    def test_all_steps_succeed(self, executor, simple_plan):
        with patch("nexus.core.executor.pyautogui.hotkey"), \
             patch("nexus.core.executor.pyautogui.write"), \
             patch("nexus.core.executor.pyautogui.click"), \
             patch("nexus.core.executor.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            results = executor.execute_plan(simple_plan.steps, task_description="test task")

        assert len(results) == len(simple_plan.steps)
        assert all(r.success for r in results)

    def test_stops_after_first_failure(self, mock_ax_walker, mock_vision, mock_verifier_success):
        mock_ax_walker.find.return_value = None
        mock_vision.find_element.return_value = None
        ex = Executor(ax=mock_ax_walker, vision=mock_vision, verifier=mock_verifier_success)

        steps = [
            ActionStep(action="click", target="GhostButton", params={}),
            ActionStep(action="type", target="", params={"text": "should not run"}),
        ]
        results = ex.execute_plan(steps, task_description="test")

        assert len(results) == 1
        assert not results[0].success

    def test_on_step_complete_callback_fires(self, executor, simple_plan):
        fired: list[tuple] = []

        def callback(current, total, result):
            fired.append((current, total))

        with patch("nexus.core.executor.pyautogui.hotkey"), \
             patch("nexus.core.executor.pyautogui.write"), \
             patch("nexus.core.executor.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            executor.execute_plan(simple_plan.steps, task_description="test", on_step_complete=callback)

        assert len(fired) == len(simple_plan.steps)

    def test_verifier_failure_marks_step_failed(self, mock_ax_walker, mock_vision, mock_verifier_failure):
        ex = Executor(ax=mock_ax_walker, vision=mock_vision, verifier=mock_verifier_failure)
        steps = [ActionStep(action="click", target="Submit", params={})]
        with patch("nexus.core.executor.pyautogui.click"):
            results = ex.execute_plan(steps, task_description="test")

        assert not results[0].success
        assert "verification failed" in results[0].reason.lower()
