"""
SQLite task memory and step cache.
Caches successful step sequences so repeat tasks run ~10x faster.
Cache key: SHA-256 of (normalized task description).
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

log = logging.getLogger(__name__)

DB_PATH = os.path.expanduser("~/Library/Application Support/Nexus/memory.db")


class Base(DeclarativeBase):
    pass


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    description = Column(Text, nullable=False)
    description_hash = Column(String(64), index=True)
    status = Column(String(20), default="pending")
    success = Column(Boolean, nullable=True)
    steps_total = Column(Integer, default=0)
    steps_completed = Column(Integer, default=0)
    duration_ms = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class StepCache(Base):
    __tablename__ = "step_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_hash = Column(String(64), index=True, nullable=False)
    steps_json = Column(Text, nullable=False)
    success_count = Column(Integer, default=1)
    last_used_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


def _task_hash(description: str) -> str:
    normalized = description.lower().strip()
    return hashlib.sha256(normalized.encode()).hexdigest()


class Memory:
    """Persistent SQLite store for task history and step caching."""

    def __init__(self, db_path: str = DB_PATH) -> None:
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(engine)
        self._Session = sessionmaker(bind=engine)

    def start_task(self, description: str) -> int:
        """Record a new task and return its ID."""
        with Session(bind=self._Session.kw["bind"]) as session:
            task = Task(
                description=description,
                description_hash=_task_hash(description),
                status="running",
            )
            session.add(task)
            session.commit()
            return task.id

    def complete_task(
        self,
        task_id: int,
        success: bool,
        steps_total: int,
        steps_completed: int,
        duration_ms: float,
    ) -> None:
        with Session(bind=self._Session.kw["bind"]) as session:
            task = session.get(Task, task_id)
            if task:
                task.status = "completed"
                task.success = success
                task.steps_total = steps_total
                task.steps_completed = steps_completed
                task.duration_ms = duration_ms
                task.completed_at = datetime.utcnow()
                session.commit()

    def cache_steps(self, task_description: str, steps: list[dict]) -> None:
        """Cache a successful step sequence for a task."""
        h = _task_hash(task_description)
        steps_json = json.dumps(steps)

        with Session(bind=self._Session.kw["bind"]) as session:
            existing = session.query(StepCache).filter_by(task_hash=h).first()
            if existing:
                existing.steps_json = steps_json
                existing.success_count += 1
                existing.last_used_at = datetime.utcnow()
            else:
                session.add(StepCache(task_hash=h, steps_json=steps_json))
            session.commit()

    def get_cached_steps(self, task_description: str) -> Optional[list[dict]]:
        """Return cached steps if available, else None."""
        h = _task_hash(task_description)
        with Session(bind=self._Session.kw["bind"]) as session:
            cached = (
                session.query(StepCache)
                .filter_by(task_hash=h)
                .order_by(StepCache.success_count.desc())
                .first()
            )
            if cached:
                log.debug("Cache hit for task hash %s (used %d times)", h[:8], cached.success_count)
                return json.loads(cached.steps_json)
        return None

    def recent_tasks(self, limit: int = 20) -> list[dict]:
        """Return recent task records for the dashboard."""
        with Session(bind=self._Session.kw["bind"]) as session:
            tasks = (
                session.query(Task)
                .order_by(Task.created_at.desc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "id": t.id,
                    "description": t.description,
                    "status": t.status,
                    "success": t.success,
                    "steps_total": t.steps_total,
                    "steps_completed": t.steps_completed,
                    "duration_ms": t.duration_ms,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                }
                for t in tasks
            ]
