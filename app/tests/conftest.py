"""
Shared pytest fixtures for NEXUS tests.
External dependencies (Anthropic API, Ollama, AX tree) are mocked by default.
Integration/e2e tests opt-in with markers.
"""
from __future__ import annotations

import os
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from nexus.core.config import Config
from nexus.core.planner import ActionStep, Plan


# ---------------------------------------------------------------------------
# Minimal test config (no real API key needed for unit tests)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def test_config() -> Config:
    return Config(
        anthropic_api_key="sk-ant-test-key",
        planner_model="claude-sonnet-4-6",
        verifier_model="claude-haiku-4-5",
        ollama_host="http://localhost:11434",
        vision_model="qwen3-vl:8b",
        max_retries=1,
        step_delay_s=0.0,
        verify_every_step=False,
        data_dir=__import__("pathlib").Path("/tmp/nexus-test"),
        log_level="WARNING",
    )


# ---------------------------------------------------------------------------
# Image fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def blank_image() -> Image.Image:
    return Image.new("RGB", (1280, 800), (0, 0, 0))


@pytest.fixture
def grey_image() -> Image.Image:
    return Image.new("RGB", (1280, 800), (80, 80, 80))


@pytest.fixture
def desktop_image() -> Image.Image:
    img = Image.new("RGB", (1280, 800), (30, 50, 100))
    return img


# ---------------------------------------------------------------------------
# Mocked AX walker
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_ax_elements() -> list:
    from nexus.core.ax_tree import AXElement
    return [
        AXElement(role="AXButton", title="Submit", value="", x=100, y=200, width=80, height=30),
        AXElement(role="AXTextField", title="Search", value="", x=200, y=50, width=300, height=32),
        AXElement(role="AXButton", title="Close", value="", x=700, y=10, width=20, height=20),
        AXElement(role="AXLink", title="Sign in", value="", x=900, y=15, width=60, height=20),
        AXElement(role="AXMenuItem", title="File", value="", x=50, y=22, width=30, height=22),
    ]


@pytest.fixture
def mock_ax_walker(mock_ax_elements):
    walker = MagicMock()
    walker.walk.return_value = mock_ax_elements
    walker.find.side_effect = lambda target, pid=None: next(
        (el for el in mock_ax_elements if target.lower() in el.label.lower()), None
    )
    walker.is_empty.return_value = False
    return walker


# ---------------------------------------------------------------------------
# Mocked vision engine
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_vision():
    from nexus.core.vision import VisionResult
    vision = MagicMock()
    vision.find_element.return_value = VisionResult(x=640, y=400, confidence="medium", raw_response="175")
    vision.describe_screen.return_value = "Safari browser showing google.com with a search field."
    return vision


# ---------------------------------------------------------------------------
# Mocked verifier
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_verifier_success():
    from nexus.core.verifier import VerificationResult
    verifier = MagicMock()
    verifier.verify.return_value = VerificationResult(success=True, reason="Action succeeded")
    verifier.verify_task_complete.return_value = VerificationResult(success=True, reason="Task complete")
    return verifier


@pytest.fixture
def mock_verifier_failure():
    from nexus.core.verifier import VerificationResult
    verifier = MagicMock()
    verifier.verify.return_value = VerificationResult(success=False, reason="Expected state not reached")
    return verifier


# ---------------------------------------------------------------------------
# Simple plan fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def simple_plan() -> Plan:
    return Plan(
        task_summary="Open Safari and navigate to google.com",
        steps=[
            ActionStep(action="focus_app", target="Safari", params={}),
            ActionStep(action="hotkey", target="", params={"keys": ["cmd", "l"]}),
            ActionStep(action="type", target="", params={"text": "google.com"}),
            ActionStep(action="hotkey", target="", params={"keys": ["return"]}),
        ],
    )


# ---------------------------------------------------------------------------
# Fixtures that skip if permissions/API not available
# ---------------------------------------------------------------------------

@pytest.fixture
def requires_api_key():
    if not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set — skipping API test")


@pytest.fixture
def requires_accessibility():
    try:
        from ApplicationServices import AXIsProcessTrusted  # type: ignore[import]
        if not AXIsProcessTrusted():
            pytest.skip("Accessibility permission not granted")
    except ImportError:
        pytest.skip("pyobjc not installed")


@pytest.fixture
def requires_ollama():
    import httpx
    try:
        r = httpx.get("http://localhost:11434", timeout=2)
        if r.status_code != 200:
            pytest.skip("Ollama not responding")
    except Exception:
        pytest.skip("Ollama not running at localhost:11434")
