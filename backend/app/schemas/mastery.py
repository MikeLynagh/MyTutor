from typing import Literal

from pydantic import BaseModel, Field


NextActionType = Literal[
    "remediate",
    "repeat_with_new_example",
    "practical_check",
    "advance",
]


class MasteryState(BaseModel):
    objective_id: str
    p_mastery: float = Field(ge=0, le=1)
    attempts: int = Field(ge=0)
    recent_errors: list[str] = Field(default_factory=list)
    last_feedback: str | None = None


class MasteryUpdate(BaseModel):
    objective_id: str
    mastery_before: float = Field(ge=0, le=1)
    mastery_after: float = Field(ge=0, le=1)


class NextAction(BaseModel):
    type: NextActionType
    reason: str
