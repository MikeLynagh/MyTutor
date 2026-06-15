from pydantic import BaseModel
from typing import Literal

class MissionCreate(BaseModel):
    goal: str
    why: str
    success_criteria: str
    current_level: Literal["beginner", "some_knowledge", "comfortable"]
    learning_preference: Literal["short", "quiz_often", "step_by_step"]
    source_mode: Literal["web", "user_material", "both"]
