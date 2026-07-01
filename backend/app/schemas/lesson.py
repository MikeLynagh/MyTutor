from pydantic import BaseModel, Field

from app.schemas.plan import AssessmentType


class Assessment(BaseModel):
    type: AssessmentType
    question: str
    expected_answer: str | None = None
    rubric: list[str] = Field(default_factory=list)
    options: list[str] = Field(default_factory=list)


class PracticalTask(BaseModel):
    instruction: str
    success_criteria: str


class LessonArtifact(BaseModel):
    lesson_id: str
    objective_id: str
    title: str
    lesson_html: str
    key_points: list[str] = Field(default_factory=list)
    practical_task: PracticalTask
    assessment: Assessment


class LessonStartResponse(BaseModel):
    mission_id: str
    objective_id: str
    lesson: LessonArtifact
