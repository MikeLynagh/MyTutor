from pydantic import BaseModel, Field

from app.schemas.mastery import NextLearningTask


class ObjectiveMasteryState(BaseModel):
    objective_id: str
    # probability from 0 to 1, likeliness to know objective
    p_mastery: float = Field(default=0.1, ge=0, le=1)
    attempts: int = Field(default=0, ge=0)
    recent_errors: list[str] = Field(default_factory=list)
    last_feedback: str | None = None


class MissionLearnerState(BaseModel):
    mission_id: str
    objectives: dict[str, ObjectiveMasteryState] = Field(default_factory=dict)
    latest_next_task: NextLearningTask | None = None
