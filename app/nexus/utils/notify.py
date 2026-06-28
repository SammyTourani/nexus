"""
macOS system notifications for NEXUS.
Sends task completion notifications via osascript (no dependencies required).
"""
from __future__ import annotations

import logging
import subprocess

log = logging.getLogger(__name__)


def _osascript(script: str) -> None:
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        timeout=3,
    )
    if result.returncode != 0:
        log.debug("osascript notification failed: %s", result.stderr.strip())


def send(
    title: str,
    message: str,
    subtitle: str = "",
    sound: bool = False,
) -> None:
    """Send a macOS system notification."""
    subtitle_part = f'subtitle "{subtitle}"' if subtitle else ""
    sound_part = 'sound name "default"' if sound else ""
    parts = [f'with title "{title}"', f'"{message}"']
    if subtitle_part:
        parts.append(subtitle_part)
    if sound_part:
        parts.append(sound_part)

    script = f"display notification {' '.join(parts)}"
    try:
        _osascript(script)
    except Exception as e:
        log.debug("Notification skipped: %s", e)


def task_complete(task: str, duration_s: float) -> None:
    send(
        title="NEXUS — Task complete",
        message=task[:80],
        subtitle=f"Finished in {duration_s:.1f}s",
        sound=True,
    )


def task_failed(task: str, reason: str) -> None:
    send(
        title="NEXUS — Task failed",
        message=task[:80],
        subtitle=reason[:60],
    )
