from fastapi import APIRouter
from uuid import uuid4

from app.schemas.mission import Mission, MissionCreate

router = APIRouter()


@router.post("/missions", response_model=Mission)
def create_mission(payload: MissionCreate):
    mission_id = str(uuid4())

    return Mission(
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
