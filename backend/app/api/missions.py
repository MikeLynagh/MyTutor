from fastapi import APIRouter
from pydantic import BaseModel
from uuid import uuid4

from app.schemas.mission import MissionCreate

router = APIRouter()

class MissionResponse(BaseModel):
    id: str
    title: str
    goal: str
    why: str
    success_criteria: str
    current_level: str
    learning_preference: str
    source_mode: str
    mission_type: str

@router.post("/missions", response_model=MissionResponse)
def create_mission(payload: MissionCreate):
    mission_id = str(uuid4())

    return MissionResponse(
        id=mission_id,
        title=payload.goal,
        goal=payload.goal,
        why=payload.why,
        success_criteria=payload.success_criteria,
        current_level=payload.current_level,
        learning_preference=payload.learning_preference,
        source_mode=payload.source_mode,
        mission_type="procedural_skill",
    )
    
