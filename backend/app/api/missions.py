from fastapi import APIRouter, HTTPException
from uuid import uuid4

from app.models.memory_store import memory_store
from app.schemas.mission import Mission, MissionCreate

router = APIRouter()


@router.post("/missions", response_model=Mission)
def create_mission(payload: MissionCreate):
    mission_id = str(uuid4())

    mission = Mission(
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

    return memory_store.save_mission(mission)


@router.get("/missions/{mission_id}", response_model=Mission)
def get_mission(mission_id: str):
    mission = memory_store.get_mission(mission_id)

    if mission is None:
        raise HTTPException(status_code=404, detail="Mission not found")

    return mission
