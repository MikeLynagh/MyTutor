import json
import os
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from typing import Any, TypeVar
from uuid import uuid4

from pydantic import BaseModel

from app.models.learner import MissionLearnerState, ObjectiveMasteryState
from app.schemas.answer import AnswerSubmission
from app.schemas.evaluation import EvaluationResult
from app.schemas.lesson import LessonArtifact
from app.schemas.mastery import MasteryUpdate, NextLearningTask
from app.schemas.mission import Mission
from app.schemas.mission_plan import MissionPlanResponse

ModelT = TypeVar("ModelT", bound=BaseModel)


def _default_db_path() -> Path:
    configured_path = os.getenv("MEMORY_DB_PATH")
    if configured_path:
        return Path(configured_path).expanduser()

    return Path(__file__).resolve().parents[2] / "data" / "memory.sqlite3"


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _model_to_json(model: BaseModel) -> str:
    return json.dumps(model.model_dump(mode="json"), separators=(",", ":"), sort_keys=True)


def _json_to_model(payload: str, schema: type[ModelT]) -> ModelT:
    return schema.model_validate(json.loads(payload))


class MemoryStore:
    def __init__(self, db_path: Path | str | None = None) -> None:
        self.db_path = Path(db_path) if db_path is not None else _default_db_path()
        self._lock = RLock()
        self._missions: dict[str, Mission] = {}
        self._mission_plans: dict[str, MissionPlanResponse] = {}
        self._lessons: dict[tuple[str, str], LessonArtifact] = {}
        self._task_lessons: dict[tuple[str, str], LessonArtifact] = {}
        self._learner_states: dict[str, MissionLearnerState] = {}
        self._ensure_schema()

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
                CREATE TABLE IF NOT EXISTS missions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    goal TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS mission_plans (
                    mission_id TEXT PRIMARY KEY,
                    mission_type TEXT NOT NULL,
                    recommended_learning_approach TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS lessons (
                    mission_id TEXT NOT NULL,
                    objective_id TEXT NOT NULL,
                    lesson_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (mission_id, objective_id)
                );

                CREATE INDEX IF NOT EXISTS idx_lessons_lesson_id
                    ON lessons (lesson_id);

                CREATE TABLE IF NOT EXISTS task_lessons (
                    mission_id TEXT NOT NULL,
                    lesson_id TEXT NOT NULL,
                    objective_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (mission_id, lesson_id)
                );

                CREATE INDEX IF NOT EXISTS idx_task_lessons_objective
                    ON task_lessons (mission_id, objective_id, created_at);

                CREATE TABLE IF NOT EXISTS learner_states (
                    mission_id TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS answer_evaluations (
                    id TEXT PRIMARY KEY,
                    mission_id TEXT NOT NULL,
                    lesson_id TEXT NOT NULL,
                    objective_id TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    evaluation_json TEXT NOT NULL,
                    mastery_json TEXT NOT NULL,
                    next_task_json TEXT NOT NULL,
                    score REAL NOT NULL,
                    mastery_before REAL NOT NULL,
                    mastery_after REAL NOT NULL,
                    next_task_type TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_answer_evaluations_mission
                    ON answer_evaluations (mission_id, created_at);

                CREATE INDEX IF NOT EXISTS idx_answer_evaluations_objective
                    ON answer_evaluations (mission_id, objective_id, created_at);
                """
            )

    def save_mission(self, mission: Mission) -> Mission:
        now = _utc_now()
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO missions (id, title, goal, payload_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title = excluded.title,
                    goal = excluded.goal,
                    payload_json = excluded.payload_json,
                    updated_at = excluded.updated_at
                """,
                (mission.id, mission.title, mission.goal, _model_to_json(mission), now, now),
            )
            self._missions[mission.id] = mission
        return mission

    def get_mission(self, mission_id: str) -> Mission | None:
        mission = self._missions.get(mission_id)
        if mission is not None:
            return mission

        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM missions WHERE id = ?",
                (mission_id,),
            ).fetchone()

        if row is None:
            return None

        mission = _json_to_model(row["payload_json"], Mission)
        self._missions[mission_id] = mission
        return mission

    def save_mission_plan(self, mission_id: str, mission_plan: MissionPlanResponse) -> MissionPlanResponse:
        now = _utc_now()
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO mission_plans (
                    mission_id,
                    mission_type,
                    recommended_learning_approach,
                    payload_json,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(mission_id) DO UPDATE SET
                    mission_type = excluded.mission_type,
                    recommended_learning_approach = excluded.recommended_learning_approach,
                    payload_json = excluded.payload_json,
                    updated_at = excluded.updated_at
                """,
                (
                    mission_id,
                    mission_plan.mission_type,
                    mission_plan.recommended_learning_approach,
                    _model_to_json(mission_plan),
                    now,
                    now,
                ),
            )
            self._mission_plans[mission_id] = mission_plan
        return mission_plan

    def get_mission_plan(self, mission_id: str) -> MissionPlanResponse | None:
        mission_plan = self._mission_plans.get(mission_id)
        if mission_plan is not None:
            return mission_plan

        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM mission_plans WHERE mission_id = ?",
                (mission_id,),
            ).fetchone()

        if row is None:
            return None

        mission_plan = _json_to_model(row["payload_json"], MissionPlanResponse)
        self._mission_plans[mission_id] = mission_plan
        return mission_plan

    def save_lesson(self, mission_id: str, lesson: LessonArtifact) -> LessonArtifact:
        now = _utc_now()
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO lessons (
                    mission_id,
                    objective_id,
                    lesson_id,
                    title,
                    payload_json,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(mission_id, objective_id) DO UPDATE SET
                    lesson_id = excluded.lesson_id,
                    title = excluded.title,
                    payload_json = excluded.payload_json,
                    updated_at = excluded.updated_at
                """,
                (
                    mission_id,
                    lesson.objective_id,
                    lesson.lesson_id,
                    lesson.title,
                    _model_to_json(lesson),
                    now,
                    now,
                ),
            )
        self._lessons[(mission_id, lesson.objective_id)] = lesson
        return lesson

    def save_task_lesson(self, mission_id: str, lesson: LessonArtifact) -> LessonArtifact:
        now = _utc_now()
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO task_lessons (
                    mission_id,
                    lesson_id,
                    objective_id,
                    title,
                    payload_json,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(mission_id, lesson_id) DO UPDATE SET
                    objective_id = excluded.objective_id,
                    title = excluded.title,
                    payload_json = excluded.payload_json
                """,
                (
                    mission_id,
                    lesson.lesson_id,
                    lesson.objective_id,
                    lesson.title,
                    _model_to_json(lesson),
                    now,
                ),
            )
            self._task_lessons[(mission_id, lesson.lesson_id)] = lesson
        return lesson

    def get_lesson(self, mission_id: str, objective_id: str) -> LessonArtifact | None:
        lesson = self._lessons.get((mission_id, objective_id))
        if lesson is not None:
            return lesson

        with self._lock, self._connect() as connection:
            row = connection.execute(
                """
                SELECT payload_json
                FROM lessons
                WHERE mission_id = ? AND objective_id = ?
                """,
                (mission_id, objective_id),
            ).fetchone()

        if row is None:
            return None

        lesson = _json_to_model(row["payload_json"], LessonArtifact)
        self._lessons[(mission_id, objective_id)] = lesson
        return lesson

    def get_lesson_by_id(self, mission_id: str, lesson_id: str) -> LessonArtifact | None:
        for (cached_mission_id, _), lesson in self._lessons.items():
            if cached_mission_id == mission_id and lesson.lesson_id == lesson_id:
                return lesson

        task_lesson = self._task_lessons.get((mission_id, lesson_id))
        if task_lesson is not None:
            return task_lesson

        with self._lock, self._connect() as connection:
            row = connection.execute(
                """
                SELECT payload_json
                FROM task_lessons
                WHERE mission_id = ? AND lesson_id = ?
                """,
                (mission_id, lesson_id),
            ).fetchone()

        if row is None:
            return None

        lesson = _json_to_model(row["payload_json"], LessonArtifact)
        self._task_lessons[(mission_id, lesson_id)] = lesson
        return lesson

    def get_learner_state(self, mission_id: str) -> MissionLearnerState:
        learner_state = self._learner_states.get(mission_id)
        if learner_state is not None:
            return learner_state

        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM learner_states WHERE mission_id = ?",
                (mission_id,),
            ).fetchone()

        if row is not None:
            learner_state = _json_to_model(row["payload_json"], MissionLearnerState)
        else:
            learner_state = MissionLearnerState(mission_id=mission_id)
            self._persist_learner_state(learner_state)

        self._learner_states[mission_id] = learner_state
        return learner_state

    def get_objective_mastery(self, mission_id: str, objective_id: str) -> ObjectiveMasteryState:
        learner_state = self.get_learner_state(mission_id)
        objective_state = learner_state.objectives.get(objective_id)
        if objective_state is None:
            objective_state = ObjectiveMasteryState(objective_id=objective_id)
            learner_state.objectives[objective_id] = objective_state
            self._persist_learner_state(learner_state)
        return objective_state

    def save_objective_mastery(
        self,
        mission_id: str,
        objective_state: ObjectiveMasteryState,
    ) -> ObjectiveMasteryState:
        learner_state = self.get_learner_state(mission_id)
        learner_state.objectives[objective_state.objective_id] = objective_state
        self._persist_learner_state(learner_state)
        return objective_state

    def save_latest_next_task(
        self,
        mission_id: str,
        next_task: NextLearningTask,
    ) -> NextLearningTask:
        learner_state = self.get_learner_state(mission_id)
        learner_state.latest_next_task = next_task
        self._persist_learner_state(learner_state)
        return next_task

    def get_latest_next_task(self, mission_id: str) -> NextLearningTask | None:
        learner_state = self.get_learner_state(mission_id)
        return learner_state.latest_next_task

    def save_answer_evaluation(
        self,
        *,
        mission_id: str,
        submission: AnswerSubmission,
        evaluation: EvaluationResult,
        mastery: MasteryUpdate,
        next_task: NextLearningTask,
    ) -> dict[str, Any]:
        record = {
            "id": str(uuid4()),
            "mission_id": mission_id,
            "lesson_id": submission.lesson_id,
            "objective_id": submission.objective_id,
            "answer": submission.answer,
            "evaluation": evaluation.model_dump(mode="json"),
            "mastery": mastery.model_dump(mode="json"),
            "next_task": next_task.model_dump(mode="json"),
            "created_at": _utc_now(),
        }

        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO answer_evaluations (
                    id,
                    mission_id,
                    lesson_id,
                    objective_id,
                    answer,
                    evaluation_json,
                    mastery_json,
                    next_task_json,
                    score,
                    mastery_before,
                    mastery_after,
                    next_task_type,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["id"],
                    mission_id,
                    submission.lesson_id,
                    submission.objective_id,
                    submission.answer,
                    json.dumps(record["evaluation"], separators=(",", ":"), sort_keys=True),
                    json.dumps(record["mastery"], separators=(",", ":"), sort_keys=True),
                    json.dumps(record["next_task"], separators=(",", ":"), sort_keys=True),
                    evaluation.score,
                    mastery.mastery_before,
                    mastery.mastery_after,
                    next_task.type,
                    record["created_at"],
                ),
            )

        return record

    def get_answer_evaluation_history(self, mission_id: str) -> list[dict[str, Any]]:
        with self._lock, self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    mission_id,
                    lesson_id,
                    objective_id,
                    answer,
                    evaluation_json,
                    mastery_json,
                    next_task_json,
                    created_at
                FROM answer_evaluations
                WHERE mission_id = ?
                ORDER BY created_at ASC
                """,
                (mission_id,),
            ).fetchall()

        return [
            {
                "id": row["id"],
                "mission_id": row["mission_id"],
                "lesson_id": row["lesson_id"],
                "objective_id": row["objective_id"],
                "answer": row["answer"],
                "evaluation": json.loads(row["evaluation_json"]),
                "mastery": json.loads(row["mastery_json"]),
                "next_task": json.loads(row["next_task_json"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def _persist_learner_state(self, learner_state: MissionLearnerState) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO learner_states (mission_id, payload_json, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(mission_id) DO UPDATE SET
                    payload_json = excluded.payload_json,
                    updated_at = excluded.updated_at
                """,
                (learner_state.mission_id, _model_to_json(learner_state), _utc_now()),
            )
            self._learner_states[learner_state.mission_id] = learner_state


memory_store = MemoryStore()
