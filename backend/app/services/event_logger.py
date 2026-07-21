import json
import logging
import os
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

EventType = Literal[
    "mission_created",
    "plan_created",
    "lesson_generated",
    "lesson_retrieved",
    "answer_submitted",
    "evaluation_completed",
    "mastery_updated",
    "next_task_selected",
    "next_task_started",
    "chat_response_generated",
    "fallback_used",
    "agent_error",
    "eval_run_completed",
]


class SessionEvent(BaseModel):
    event_id: str
    event_type: EventType
    mission_id: str | None = None
    objective_id: str | None = None
    lesson_id: str | None = None
    agent_name: str | None = None
    score: float | None = Field(default=None, ge=0, le=1)
    mastery_before: float | None = Field(default=None, ge=0, le=1)
    mastery_after: float | None = Field(default=None, ge=0, le=1)
    next_task_type: str | None = None
    latency_ms: int | None = Field(default=None, ge=0)
    fallback_used: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str


def default_event_db_path() -> Path:
    configured_path = os.getenv("MEMORY_DB_PATH")
    if configured_path:
        return Path(configured_path).expanduser()

    return Path(__file__).resolve().parents[2] / "data" / "memory.sqlite3"


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class EventLogger:
    def __init__(self, db_path: Path | str | None = None) -> None:
        self.db_path = Path(db_path) if db_path is not None else default_event_db_path()
        self._lock = RLock()
        self._ensure_schema()

    def log_event(
        self,
        *,
        event_type: EventType,
        mission_id: str | None = None,
        objective_id: str | None = None,
        lesson_id: str | None = None,
        agent_name: str | None = None,
        score: float | None = None,
        mastery_before: float | None = None,
        mastery_after: float | None = None,
        next_task_type: str | None = None,
        latency_ms: int | None = None,
        fallback_used: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> SessionEvent | None:
        event = SessionEvent(
            event_id=str(uuid4()),
            event_type=event_type,
            mission_id=mission_id,
            objective_id=objective_id,
            lesson_id=lesson_id,
            agent_name=agent_name,
            score=score,
            mastery_before=mastery_before,
            mastery_after=mastery_after,
            next_task_type=next_task_type,
            latency_ms=latency_ms,
            fallback_used=fallback_used,
            metadata=metadata or {},
            created_at=utc_now(),
        )

        try:
            with self._lock, self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO session_events (
                        event_id,
                        event_type,
                        mission_id,
                        objective_id,
                        lesson_id,
                        agent_name,
                        score,
                        mastery_before,
                        mastery_after,
                        next_task_type,
                        latency_ms,
                        fallback_used,
                        metadata_json,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event.event_id,
                        event.event_type,
                        event.mission_id,
                        event.objective_id,
                        event.lesson_id,
                        event.agent_name,
                        event.score,
                        event.mastery_before,
                        event.mastery_after,
                        event.next_task_type,
                        event.latency_ms,
                        int(event.fallback_used),
                        json.dumps(event.metadata, separators=(",", ":"), sort_keys=True),
                        event.created_at,
                    ),
                )
        except sqlite3.Error:
            logger.exception("Failed to write session event %s", event.event_type)
            return None

        return event

    def list_events(self, mission_id: str | None = None, limit: int = 100) -> list[SessionEvent]:
        query = """
            SELECT
                event_id,
                event_type,
                mission_id,
                objective_id,
                lesson_id,
                agent_name,
                score,
                mastery_before,
                mastery_after,
                next_task_type,
                latency_ms,
                fallback_used,
                metadata_json,
                created_at
            FROM session_events
        """
        params: list[Any] = []
        if mission_id is not None:
            query += " WHERE mission_id = ?"
            params.append(mission_id)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with self._lock, self._connect() as connection:
            rows = connection.execute(query, params).fetchall()

        return [
            SessionEvent(
                event_id=row["event_id"],
                event_type=row["event_type"],
                mission_id=row["mission_id"],
                objective_id=row["objective_id"],
                lesson_id=row["lesson_id"],
                agent_name=row["agent_name"],
                score=row["score"],
                mastery_before=row["mastery_before"],
                mastery_after=row["mastery_after"],
                next_task_type=row["next_task_type"],
                latency_ms=row["latency_ms"],
                fallback_used=bool(row["fallback_used"]),
                metadata=json.loads(row["metadata_json"]),
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=10)
        connection.row_factory = sqlite3.Row
        return connection

    def _ensure_schema(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock, self._connect() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS session_events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    mission_id TEXT,
                    objective_id TEXT,
                    lesson_id TEXT,
                    agent_name TEXT,
                    score REAL,
                    mastery_before REAL,
                    mastery_after REAL,
                    next_task_type TEXT,
                    latency_ms INTEGER,
                    fallback_used INTEGER NOT NULL DEFAULT 0,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_session_events_mission_created
                    ON session_events (mission_id, created_at);

                CREATE INDEX IF NOT EXISTS idx_session_events_type_created
                    ON session_events (event_type, created_at);
                """
            )


event_logger = EventLogger()
