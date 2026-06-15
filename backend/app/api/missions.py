from fastapi import APIRouter
from app.schemas.mission import MissionCreate

router = APIRouter()

@router.post("/missions")
def create_mission(payload: MissionCreate):
    return {
        "id": "mission_demo_1",
        "title": payload.goal,
        "goal": payload.goal,
        "why": payload.why,
        "successCriteria": payload.success_criteria,
        "currentLevel": payload.current_level,
        "learningPreference": payload.learning_preference,
        "sourceMode": payload.source_mode,
        "missionType": "procedural_skill"
    }