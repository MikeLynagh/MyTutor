from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.mastery import NextLearningTask
from app.schemas.plan import AssessmentType


ObjectiveProgressStatus = Literal["not_started", "in_progress", "mastered"]


class ObjectiveProgress(BaseModel):
    objective_id: str
    title: str
    description: str
    assessment_type: AssessmentType
    success_criteria: str
    mastery: float = Field(ge=0, le=1)
    attempts: int = Field(ge=0)
    status: ObjectiveProgressStatus
    recent_errors: list[str] = Field(default_factory=list)
    last_feedback: str | None = None


class MissionProgressResponse(BaseModel):
    mission_id: str
    overall_mastery: float = Field(ge=0, le=1)
    current_next_task: NextLearningTask | None = None
    objectives: list[ObjectiveProgress]
