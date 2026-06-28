"""
macOS TCC permission checking for NEXUS.
Reports the status of Screen Recording and Accessibility grants before the agent starts,
so users get a clear error rather than a confusing runtime failure.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from enum import Enum


class PermissionStatus(str, Enum):
    GRANTED = "granted"
    DENIED = "denied"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Permission:
    name: str
    status: PermissionStatus
    settings_url: str

    @property
    def granted(self) -> bool:
        return self.status == PermissionStatus.GRANTED

    def __str__(self) -> str:
        icon = "✓" if self.granted else "✗"
        return f"{icon} {self.name}: {self.status.value}"


def check_accessibility() -> Permission:
    """Check whether the Accessibility (AX) TCC permission is granted."""
    try:
        from ApplicationServices import AXIsProcessTrusted  # type: ignore[import]
        granted = bool(AXIsProcessTrusted())
        status = PermissionStatus.GRANTED if granted else PermissionStatus.DENIED
    except ImportError:
        status = PermissionStatus.UNKNOWN

    return Permission(
        name="Accessibility",
        status=status,
        settings_url=(
            "x-apple.systempreferences:"
            "com.apple.preference.security?Privacy_Accessibility"
        ),
    )


def check_screen_recording() -> Permission:
    """
    Detect Screen Recording permission by capturing a frame and checking
    whether it contains non-black content.
    macOS returns an all-black frame when Screen Recording is denied.
    """
    try:
        from nexus.core.screenshot import capture
        shot = capture()
        granted = not shot.is_blank()
        status = PermissionStatus.GRANTED if granted else PermissionStatus.DENIED
    except Exception:
        status = PermissionStatus.UNKNOWN

    return Permission(
        name="Screen Recording",
        status=status,
        settings_url=(
            "x-apple.systempreferences:"
            "com.apple.preference.security?Privacy_ScreenCapture"
        ),
    )


def open_settings(permission: Permission) -> None:
    """Open the relevant System Settings pane for a denied permission."""
    subprocess.run(["open", permission.settings_url], check=False)


@dataclass
class PermissionReport:
    accessibility: Permission
    screen_recording: Permission

    @property
    def all_granted(self) -> bool:
        return self.accessibility.granted and self.screen_recording.granted

    @property
    def missing(self) -> list[Permission]:
        return [p for p in (self.accessibility, self.screen_recording) if not p.granted]

    def __str__(self) -> str:
        lines = ["NEXUS Permission Status:", f"  {self.accessibility}", f"  {self.screen_recording}"]
        if not self.all_granted:
            lines.append("")
            lines.append("Grant missing permissions in System Settings, then restart NEXUS.")
        return "\n".join(lines)


def check_all() -> PermissionReport:
    return PermissionReport(
        accessibility=check_accessibility(),
        screen_recording=check_screen_recording(),
    )
