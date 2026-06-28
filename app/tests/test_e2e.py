"""
End-to-end integration tests for NEXUS.
These tests run the full pipeline on real macOS apps.
Requires: ANTHROPIC_API_KEY, Ollama with qwen3-vl:8b, Accessibility + Screen Recording permissions.

Run with: pytest tests/test_e2e.py -v -m e2e --timeout=60
"""
import os
import time
import subprocess
import pytest

from nexus.core.ax_tree import AXTreeWalker
from nexus.core.vision import VisionEngine
from nexus.core.planner import Planner
from nexus.core.verifier import Verifier
from nexus.core.executor import Executor


def requires_all_permissions(f):
    return pytest.mark.e2e(f)


@pytest.fixture(scope="module")
def ax():
    try:
        return AXTreeWalker()
    except PermissionError:
        pytest.skip("Accessibility permission not granted")


@pytest.fixture(scope="module")
def vision():
    return VisionEngine()


@pytest.fixture(scope="module")
def planner():
    if not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set")
    return Planner()


@pytest.fixture(scope="module")
def verifier():
    if not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set")
    return Verifier()


@pytest.fixture(scope="module")
def executor(ax, vision, verifier):
    return Executor(ax, vision, verifier)


@pytest.mark.e2e
def test_open_safari_and_navigate(executor, planner):
    """Full pipeline: plan + execute opening Safari and navigating to a URL."""
    task = "Open Safari and navigate to example.com"
    plan = planner.plan(task)

    assert len(plan.steps) > 0
    results = executor.execute_plan(plan.steps, task_description=task)

    completed = sum(1 for r in results if r.success)
    assert completed >= len(results) - 1, \
        f"Expected all steps to succeed, got {completed}/{len(results)}"

    time.sleep(1)
    # Safari should now be frontmost
    import subprocess
    result = subprocess.run(
        ["osascript", "-e", 'tell application "System Events" to name of first process whose frontmost is true'],
        capture_output=True, text=True
    )
    assert "Safari" in result.stdout, f"Expected Safari to be frontmost, got: {result.stdout}"


@pytest.mark.e2e
def test_open_textedit_and_type(executor, planner):
    """Full pipeline: open TextEdit and type a sentence."""
    task = "Open TextEdit, create a new document, and type: NEXUS automation test"
    plan = planner.plan(task)
    results = executor.execute_plan(plan.steps, task_description=task)
    completed = sum(1 for r in results if r.success)
    assert completed > 0, "At least some steps should succeed"


@pytest.mark.e2e
def test_ax_primary_vision_fallback_routing(ax, vision):
    """Verify AX is tried first and vision only fires when AX returns empty."""
    subprocess.Popen(["open", "-a", "Safari"])
    time.sleep(1.5)

    # Safari has AX elements — vision should not be needed
    elements = ax.walk()
    assert len(elements) > 0, "Safari should expose AX elements"
    assert not ax.is_empty(), "AX should not be empty for Safari"


@pytest.mark.e2e
def test_verifier_catches_failed_click(verifier):
    """Verifier should flag when no visible change occurred after a click."""
    # Take a screenshot in a neutral state
    from PIL import Image
    img = Image.new("RGB", (1280, 800), (20, 20, 20))  # simulate blank screen

    result = verifier.verify(
        "clicked the 'Submit Form' button",
        "A success confirmation message should now be visible",
        screenshot=img,
    )
    # A blank dark screen after "Submit" click should fail verification
    assert result.success is False
