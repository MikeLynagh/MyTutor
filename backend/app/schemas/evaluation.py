from pydantic import BaseModel, Field


class EvaluationResult(BaseModel):
    is_correct: bool
    score: float = Field(ge=0, le=1)
    feedback: str
    misconception: str | None = None
    missing_points: list[str] = Field(default_factory=list)
    next_hint: str | None = None
