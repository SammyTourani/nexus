"""
AX tree walker for macOS accessibility API.
Primary element detection interface — always attempted before vision.
Reads a focused window's interactive elements in 30-80ms via pyobjc.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Optional

import objc
from ApplicationServices import (
    AXIsProcessTrusted,
    AXUIElementCopyAttributeValue,
    AXUIElementCreateApplication,
    kAXErrorSuccess,
)
from AppKit import NSWorkspace

log = logging.getLogger(__name__)

# Roles that the user can meaningfully interact with
INTERACTIVE_ROLES = frozenset({
    "AXButton",
    "AXCheckBox",
    "AXRadioButton",
    "AXTextField",
    "AXTextArea",
    "AXComboBox",
    "AXPopUpButton",
    "AXMenuItem",
    "AXMenuBarItem",
    "AXLink",
    "AXCell",
    "AXRow",
    "AXTab",
    "AXScrollBar",
    "AXSlider",
    "AXStepper",
    "AXIncrementor",
    "AXSearchField",
    "AXColorWell",
})


@dataclass
class AXElement:
    role: str
    title: str
    value: str
    x: float
    y: float
    width: float
    height: float
    enabled: bool = True

    @property
    def cx(self) -> float:
        return self.x + self.width / 2

    @property
    def cy(self) -> float:
        return self.y + self.height / 2

    @property
    def label(self) -> str:
        return self.title or self.value or self.role

    def __repr__(self) -> str:
        return f"AXElement({self.role} '{self.label}' @ ({self.cx:.0f},{self.cy:.0f}))"


def _get_attr(element, attr: str):
    err, value = AXUIElementCopyAttributeValue(element, attr, None)
    if err == kAXErrorSuccess:
        return value
    return None


def _walk(element, depth: int = 0, max_depth: int = 10) -> list[AXElement]:
    if depth > max_depth:
        return []

    role = _get_attr(element, "AXRole") or ""
    title = str(_get_attr(element, "AXTitle") or "")
    value = _get_attr(element, "AXValue")
    value_str = str(value) if value is not None and not hasattr(value, "x") else ""
    enabled = _get_attr(element, "AXEnabled")
    position = _get_attr(element, "AXPosition")
    size = _get_attr(element, "AXSize")

    results: list[AXElement] = []

    if role in INTERACTIVE_ROLES and position and size and (title or value_str):
        results.append(AXElement(
            role=role,
            title=title,
            value=value_str if value_str != title else "",
            x=float(position.x),
            y=float(position.y),
            width=float(size.width),
            height=float(size.height),
            enabled=bool(enabled) if enabled is not None else True,
        ))

    children = _get_attr(element, "AXChildren") or []
    for child in children:
        results.extend(_walk(child, depth + 1, max_depth))

    return results


class AXTreeWalker:
    """
    Walks the macOS Accessibility tree for the frontmost application.
    Requires Accessibility permission in System Settings > Privacy & Security.
    """

    def __init__(self) -> None:
        if not AXIsProcessTrusted():
            raise PermissionError(
                "Accessibility permission not granted. "
                "Open System Settings > Privacy & Security > Accessibility "
                "and enable Nexus."
            )

    def get_frontmost_pid(self) -> Optional[int]:
        app = NSWorkspace.sharedWorkspace().frontmostApplication()
        if app:
            return int(app.processIdentifier())
        return None

    def get_frontmost_name(self) -> Optional[str]:
        app = NSWorkspace.sharedWorkspace().frontmostApplication()
        if app:
            return str(app.localizedName())
        return None

    def walk(self, pid: Optional[int] = None) -> list[AXElement]:
        """Return all interactive elements for the given PID (or frontmost app)."""
        target_pid = pid or self.get_frontmost_pid()
        if not target_pid:
            return []

        t0 = time.perf_counter()
        app_el = AXUIElementCreateApplication(target_pid)
        elements = _walk(app_el)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        log.debug("AX walk: %d elements in %.1fms (PID %d)", len(elements), elapsed_ms, target_pid)
        return elements

    def find(self, target: str, pid: Optional[int] = None) -> Optional[AXElement]:
        """
        Find the best-matching interactive element for a plain-English target description.
        Returns None if no reasonable match found (caller should fall back to vision).
        """
        elements = [el for el in self.walk(pid) if el.enabled]
        if not elements:
            return None

        target_lower = target.lower().strip()

        # 1. Exact label match
        for el in elements:
            if el.label.lower() == target_lower:
                return el

        # 2. Contains match
        for el in elements:
            if target_lower in el.label.lower():
                return el

        # 3. All words present
        words = target_lower.split()
        scored = []
        for el in elements:
            label_lower = el.label.lower()
            score = sum(1 for w in words if w in label_lower)
            if score > 0:
                scored.append((score, el))

        if scored:
            scored.sort(key=lambda x: x[0], reverse=True)
            return scored[0][1]

        return None

    def is_empty(self, pid: Optional[int] = None) -> bool:
        """True when the frontmost app exposes no interactive AX elements (Qt apps, web canvases)."""
        return len(self.walk(pid)) == 0
