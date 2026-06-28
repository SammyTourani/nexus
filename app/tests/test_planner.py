"""
Unit tests for the planner module.
Requires ANTHROPIC_API_KEY in environment.
"""
import os
import pytest

from nexus.core.planner import ActionStep, Plan, Planner


@pytest.fixture(scope="module")
def planner():
    if not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set")
    return Planner()


def test_plan_returns_plan_object(planner):
    plan = planner.plan("Open Safari and go to google.com")
    assert isinstance(plan, Plan)
    assert len(plan.steps) > 0
    assert plan.task_summary


def test_plan_steps_have_valid_actions(planner):
    plan = planner.plan("Open TextEdit and type Hello World")
    valid_actions = {"click", "type", "hotkey", "scroll", "focus_app", "wait", "screenshot"}
    for step in plan.steps:
        assert step.action in valid_actions, f"Invalid action: {step.action}"
        assert isinstance(step.target, str)
        assert isinstance(step.params, dict)


def test_plan_includes_focus_app_for_open_task(planner):
    plan = planner.plan("Open Calculator and compute 42 * 7")
    actions = [s.action for s in plan.steps]
    assert "focus_app" in actions, "Should include focus_app to open an application"


def test_plan_includes_type_for_search_task(planner):
    plan = planner.plan("Search Google for the latest AI news")
    actions = [s.action for s in plan.steps]
    assert "type" in actions, "Search task should include a type action"


def test_plan_handles_simple_click_task(planner):
    plan = planner.plan(
        "Click the Close button",
        screen_description="A dialog box with a Close button is visible"
    )
    assert any(s.action == "click" for s in plan.steps)


def test_replan_generates_recovery_steps(planner):
    original_task = "Search Google for AI news"
    completed = [ActionStep("focus_app", "Safari", {})]
    plan = planner.replan(
        original_task,
        completed,
        failure_reason="Address bar not found in AX tree",
        screen_description="Safari is open on a blank page"
    )
    assert len(plan.steps) > 0
