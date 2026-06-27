from pydantic import BaseModel, Field

from app.schemas.evaluation import EvaluationResult
from app.schemas.mastery import MasteryUpdate, NextAction


class AnswerSubmission(BaseModel):
    lesson_id: str
    objective_id: str
    answer: str = Field(min_length=1)


class AnswerEvaluationResponse(BaseModel):
    evaluation: EvaluationResult
    mastery: MasteryUpdate
    next_action: NextAction
