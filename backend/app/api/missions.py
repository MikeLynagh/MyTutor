from fastapi import APIRouter
from pydantic import BaseModel
from typing import Literal
from uuid import uuid4


router = APIRouter()

class MissionCreate(BaseModel):
    goal:str
    why:str
    success_criteria:str
    current_level: Literal["beginner", "some_knowledge", "comfortable"]
    learning_preference: Literal["short", "quiz_often", "step_by_step"]

class MissionResponse(BaseModel):
    id: str
    title: str
    goal: str
    why: str
    success_criteria: str
    current_level: str
    learning_preference: str
    mission_type: str

@router.post("/missions", response_model=MissionResponse)
def create_mission(payload: MissionCreate):
    mission_id = str(uuid4())

    return MissionResponse(
        id =  mission_id,
        title =  payload.goal,
        goal =  payload.goal,
        why =  payload.why,
        successCriteria = payload.success_criteria,
        currentLevel =  payload.current_level,
        learningPreference =  payload.learning_preference,
        sourceMode = payload.source_mode,
        missionType = "procedural_skill",
    )
    