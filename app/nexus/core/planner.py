"""
Task planner using Claude Sonnet 4.6.
Takes a natural language task + current screen description and returns
a structured list of action steps for the executor to carry out.
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Optional

import anthropic

log = logging.getLogger(__name__)

PLANNER_MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are NEXUS, a macOS automation agent. Your job is to break down a user's task into a precise sequence of UI actions that can be executed programmatically.

You have access to these action types:
- click: Click on a UI element by its label (button text, field name, menu item, link text)
- type: Type text into the currently focused field
- hotkey: Press a keyboard shortcut (e.g. cmd+t, cmd+s, escape, return, tab)
- scroll: Scroll in a direction (up/down/left/right) with an amount (1-10)
- focus_app: Switch focus to an application by name
- wait: Wait for a condition to appear (describe what to wait for)
- screenshot: Take a screenshot to assess current state (use sparingly)

Rules:
1. Be specific with click targets — use the exact text that would appear on the button, menu, or link
2. If an app needs to be opened first, start with focus_app
3. Break complex steps into simple atomic actions
4. For web browsing, assume the user's default browser is open unless told otherwise
5. Return ONLY valid JSON — no commentary, no markdown fences

Output format:
{
  "task_summary": "one sentence describing what this task does",
  "steps": [
    {"action": "focus_app", "target": "Safari", "params": {}},
    {"action": "hotkey", "target": "", "params": {"keys": ["cmd", "l"]}},
    {"action": "type", "target": "", "params": {"text": "google.com"}},
    {"action": "hotkey", "target": "", "params": {"keys": ["return"]}},
    {"action": "click", "target": "Search field", "params": {}}
  ]
}"""


@dataclass
class ActionStep:
    action: str
    target: str
    params: dict

    def __repr__(self) -> str:
        return f"Step({self.action} '{self.target}' {self.params})"


@dataclass
class Plan:
    task_summary: str
    steps: list[ActionStep]

    def __len__(self) -> int:
        return len(self.steps)


class Planner:
    """
    Calls Claude Sonnet 4.6 to break a user task into executable action steps.
    Called once per task (not per step) — the full plan is handed to the executor.
    """

    def __init__(self) -> None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY environment variable not set.")
        self._client = anthropic.Anthropic(api_key=api_key)

    def plan(self, task: str, screen_description: str = "", memory_hint: str = "") -> Plan:
        """
        Generate an action plan for the given task.

        Args:
            task: Natural language task description from the user.
            screen_description: Current screen state (from AX tree summary or vision describe).
            memory_hint: Cached step sequence from a previous successful run, if available.
        """
        context_parts = [f"User task: {task}"]
        if screen_description:
            context_parts.append(f"Current screen: {screen_description}")
        if memory_hint:
            context_parts.append(f"Previously successful steps for a similar task: {memory_hint}")

        user_message = "\n\n".join(context_parts)

        log.info("Planning task: %s", task)

        response = self._client.messages.create(
            model=PLANNER_MODEL,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
            thinking={"type": "adaptive"},
        )

        raw_text = response.content[-1].text.strip()
        log.debug("Planner raw response: %s", raw_text[:500])

        return self._parse_response(raw_text)

    def _parse_response(self, raw: str) -> Plan:
        # Strip markdown fences if the model added them despite instructions
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            log.error("Failed to parse planner JSON: %s\nRaw: %s", e, raw[:500])
            raise ValueError(f"Planner returned invalid JSON: {e}") from e

        steps = [
            ActionStep(
                action=s["action"],
                target=s.get("target", ""),
                params=s.get("params", {}),
            )
            for s in data.get("steps", [])
        ]

        return Plan(
            task_summary=data.get("task_summary", ""),
            steps=steps,
        )

    def replan(self, original_task: str, completed_steps: list[ActionStep], failure_reason: str, screen_description: str = "") -> Plan:
        """Generate a recovery plan after a step failure."""
        completed_text = "\n".join(f"  {i+1}. {s}" for i, s in enumerate(completed_steps))
        user_message = (
            f"Original task: {original_task}\n\n"
            f"Completed steps so far:\n{completed_text}\n\n"
            f"Failure: {failure_reason}\n\n"
            f"Current screen: {screen_description}\n\n"
            f"Generate a recovery plan to complete the original task from this point. "
            f"Do not repeat steps already successfully completed."
        )

        response = self._client.messages.create(
            model=PLANNER_MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
            thinking={"type": "adaptive"},
        )

        raw_text = response.content[-1].text.strip()
        return self._parse_response(raw_text)
