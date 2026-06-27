from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.mission import MissionType


AssessmentType = Literal[
    "short_written_answer",
    "multiple_choice",
    "practical_check",
    "free_form",
]


class Objective(BaseModel):
    id: str
    title: str
    description: str
    difficulty: float = Field(ge=0, le=1)
    assessment_type: AssessmentType
    prerequisites: list[str] = Field(default_factory=list)
    success_criteria: str


class LearningPlan(BaseModel):
    mission_type: MissionType
    objectives: list[Objective] = Field(default_factory=list)
    diagnostic_questions: list[str] = Field(default_factory=list)
