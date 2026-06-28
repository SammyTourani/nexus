"""
Unit tests for the step verifier module.
Requires ANTHROPIC_API_KEY in environment.
"""
import os
import pytest
from PIL import Image

from nexus.core.verifier import Verifier, VerificationResult


@pytest.fixture(scope="module")
def verifier():
    if not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set")
    return Verifier()


def _make_test_image(color=(30, 30, 30)) -> Image.Image:
    img = Image.new("RGB", (1280, 800), color)
    return img


def test_verifier_instantiates(verifier):
    assert verifier is not None


def test_verify_returns_result_object(verifier):
    img = _make_test_image()
    result = verifier.verify(
        "clicked Submit button",
        "A confirmation dialog or success message should be visible",
        screenshot=img,
    )
    assert isinstance(result, VerificationResult)
    assert isinstance(result.success, bool)
    assert isinstance(result.reason, str)
    assert len(result.reason) > 0


def test_verifier_detects_blank_screen_as_failure(verifier):
    img = _make_test_image(color=(0, 0, 0))
    result = verifier.verify(
        "opened Safari browser",
        "Safari browser window should be visible with navigation controls",
        screenshot=img,
    )
    assert result.success is False, "Blank black screen should not verify as Safari open"


def test_verify_task_complete_returns_result(verifier):
    img = _make_test_image()
    result = verifier.verify_task_complete(
        "Search Google for AI news and open the first result",
        screenshot=img,
    )
    assert isinstance(result, VerificationResult)
    assert isinstance(result.success, bool)
