"""
Tests for the memory and step-cache module.
All tests use a temporary SQLite database — no cleanup needed.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from nexus.core.memory import Memory


@pytest.fixture
def memory() -> Memory:
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    return Memory(db_path=db_path)


def test_start_and_complete_task(memory: Memory) -> None:
    task_id = memory.start_task("Open Safari and search for AI news")
    assert isinstance(task_id, int)
    assert task_id > 0

    memory.complete_task(
        task_id,
        success=True,
        steps_total=4,
        steps_completed=4,
        duration_ms=1250.0,
    )

    tasks = memory.recent_tasks()
    assert len(tasks) == 1
    assert tasks[0]["success"] is True
    assert tasks[0]["steps_total"] == 4
    assert tasks[0]["duration_ms"] == pytest.approx(1250.0)


def test_cache_and_retrieve_steps(memory: Memory) -> None:
    task = "Search Google for quarterly earnings"
    steps = [
        {"action": "focus_app", "target": "Safari", "params": {}},
        {"action": "type", "target": "", "params": {"text": "quarterly earnings"}},
        {"action": "hotkey", "target": "", "params": {"keys": ["return"]}},
    ]

    memory.cache_steps(task, steps)
    cached = memory.get_cached_steps(task)

    assert cached is not None
    assert len(cached) == 3
    assert cached[0]["action"] == "focus_app"


def test_cache_is_case_and_whitespace_insensitive(memory: Memory) -> None:
    task_a = "open safari and go to google.com"
    task_b = "  Open Safari And Go To Google.com  "
    steps = [{"action": "focus_app", "target": "Safari", "params": {}}]

    memory.cache_steps(task_a, steps)
    result = memory.get_cached_steps(task_b)

    assert result is not None


def test_cache_miss_returns_none(memory: Memory) -> None:
    result = memory.get_cached_steps("a task that was never cached before xyz123")
    assert result is None


def test_recent_tasks_respects_limit(memory: Memory) -> None:
    for i in range(25):
        task_id = memory.start_task(f"Task number {i}")
        memory.complete_task(task_id, success=True, steps_total=1, steps_completed=1, duration_ms=100)

    tasks = memory.recent_tasks(limit=10)
    assert len(tasks) == 10


def test_multiple_failed_tasks_tracked(memory: Memory) -> None:
    for i in range(3):
        task_id = memory.start_task(f"Failed task {i}")
        memory.complete_task(task_id, success=False, steps_total=5, steps_completed=i, duration_ms=500)

    tasks = memory.recent_tasks()
    failed = [t for t in tasks if t["success"] is False]
    assert len(failed) == 3


def test_task_status_default_is_pending(memory: Memory) -> None:
    task_id = memory.start_task("Pending task")
    tasks = memory.recent_tasks()
    assert tasks[0]["status"] == "running"


def test_cache_updates_on_repeated_success(memory: Memory) -> None:
    task = "Click the Submit button"
    steps_v1 = [{"action": "click", "target": "Submit", "params": {}}]
    steps_v2 = [
        {"action": "focus_app", "target": "Safari", "params": {}},
        {"action": "click", "target": "Submit", "params": {}},
    ]

    memory.cache_steps(task, steps_v1)
    memory.cache_steps(task, steps_v2)
    result = memory.get_cached_steps(task)

    assert result is not None
    assert len(result) == 2
