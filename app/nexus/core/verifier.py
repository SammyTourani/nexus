"""
Step verifier using Claude Haiku 4.5.
Called after every executor action to confirm success before proceeding.
Fast and cheap — designed to catch failures early and prevent cascading errors.
"""
from __future__ import annotations

import base64
import io
import logging
import os
from dataclasses import dataclass
from typing import Optional

import anthropic
import mss
from PIL import Image

log = logging.getLogger(__name__)

VERIFIER_MODEL = "claude-haiku-4-5"

VERIFY_SYSTEM = """You are verifying whether a macOS UI action succeeded.
You will see a screenshot taken immediately after an action was executed.
Respond with exactly one of:
  SUCCESS: <brief reason>
  FAILURE: <brief reason>
Do not output anything else."""


@dataclass
class VerificationResult:
    success: bool
    reason: str
    screenshot: Optional[Image.Image] = None


def _capture_screen() -> Image.Image:
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        shot = sct.grab(monitor)
        return Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")


def _encode_image(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


class Verifier:
    """
    Calls Claude Haiku 4.5 with a post-action screenshot to verify success.
    Returns a VerificationResult so the executor can retry or proceed.
    """

    def __init__(self) -> None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY environment variable not set.")
        self._client = anthropic.Anthropic(api_key=api_key)

    def verify(
        self,
        action_description: str,
        expected_outcome: str,
        screenshot: Optional[Image.Image] = None,
    ) -> VerificationResult:
        """
        Verify that an action produced the expected outcome.

        Args:
            action_description: What action was just taken (e.g. "clicked Search button").
            expected_outcome: What the screen should show if the action succeeded.
            screenshot: Post-action screenshot. Captured fresh if not provided.
        """
        img = screenshot or _capture_screen()

        user_message = (
            f"Action taken: {action_description}\n"
            f"Expected outcome: {expected_outcome}\n\n"
            f"Look at the screenshot and determine if the action succeeded."
        )

        response = self._client.messages.create(
            model=VERIFIER_MODEL,
            max_tokens=100,
            system=VERIFY_SYSTEM,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": _encode_image(img),
                        },
                    },
                    {"type": "text", "text": user_message},
                ],
            }],
        )

        raw = response.content[0].text.strip()
        log.debug("Verifier response: %s", raw)

        success = raw.upper().startswith("SUCCESS")
        reason = raw.split(":", 1)[1].strip() if ":" in raw else raw

        return VerificationResult(success=success, reason=reason, screenshot=img)

    def verify_task_complete(self, task_description: str, screenshot: Optional[Image.Image] = None) -> VerificationResult:
        """Final check: did the full task complete successfully?"""
        img = screenshot or _capture_screen()

        user_message = (
            f"The following automation task was just executed: {task_description}\n\n"
            f"Look at the current screen state and determine if the task completed successfully."
        )

        response = self._client.messages.create(
            model=VERIFIER_MODEL,
            max_tokens=150,
            system=VERIFY_SYSTEM,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": _encode_image(img),
                        },
                    },
                    {"type": "text", "text": user_message},
                ],
            }],
        )

        raw = response.content[0].text.strip()
        success = raw.upper().startswith("SUCCESS")
        reason = raw.split(":", 1)[1].strip() if ":" in raw else raw
        return VerificationResult(success=success, reason=reason, screenshot=img)
