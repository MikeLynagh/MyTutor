from typing import Literal

from pydantic import BaseModel


CurrentLevel = Literal["beginner", "some_knowledge", "comfortable"]
LearningPreference = Literal["short", "quiz_often", "step_by_step"]
SourceMode = Literal["web", "user_material", "both"]
MissionType = Literal[
    "procedural_skill",
    "technical_skill",
    "conceptual_topic",
    "interview_prep",
]


class MissionCreate(BaseModel):
    goal: str
    why: str
    success_criteria: str
    current_level: CurrentLevel
    learning_preference: LearningPreference
    source_mode: SourceMode = "web"


class Mission(BaseModel):
    id: str
    title: str
    goal: str
    why: str
    success_criteria: str
    current_level: CurrentLevel
    learning_preference: LearningPreference
    source_mode: SourceMode
    mission_type: MissionType
