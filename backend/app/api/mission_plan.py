from fastapi import APIRouter

from app.agents.resource_curator import ResourceCuratorAgent
from app.schemas.mission_plan import MissionPlanRequest, MissionPlanResponse

router = APIRouter()

resource_curator = ResourceCuratorAgent()

@router.post("/missions/{mission_id}/plan", response_model=MissionPlanResponse)
def create_mission_plan(mission_id: str, payload: MissionPlanRequest):
    curated = resource_curator.curate(
        goal=payload.goal,
        source_mode=payload.source_mode,
        user_material=payload.user_material,
    )

    return MissionPlanResponse(
        mission_id=mission_id,
        sources=curated["sources"],
        summary=curated["summary"],
    )
