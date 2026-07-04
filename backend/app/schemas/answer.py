from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.evaluation import EvaluationResult
from app.schemas.mastery import MasteryUpdate, NextAction


class AnswerSubmission(BaseModel):
    lesson_id: str
    objective_id: str
    answer: str = Field(min_length=1)

    @field_validator("answer")
    @classmethod
    def answer_must_not_be_blank(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Answer must not be blank")
        return normalized


class AnswerSubmissionResponse(BaseModel):
    lesson_id: str
    objective_id: str
    answer: str
    status: Literal["received"]
    message: str


class AnswerEvaluationResponse(BaseModel):
    evaluation: EvaluationResult
    mastery: MasteryUpdate
    next_action: NextAction


class AnswerEvaluationWithMasteryResponse(BaseModel):
    evaluation: EvaluationResult
    mastery: MasteryUpdate