from fastapi import APIRouter

from app.agents.resource_curator import ResourceCuratorAgent
from app.models.memory_store import memory_store
from app.schemas.mission_plan import MissionPlanRequest, MissionPlanResponse

router = APIRouter()

resource_curator = ResourceCuratorAgent()

@router.post("/missions/{mission_id}/plan", response_model=MissionPlanResponse)
def create_mission_plan(mission_id: str, payload: MissionPlanRequest):
    mission = memory_store.get_mission(mission_id)
    curated = resource_curator.curate(
        goal=payload.goal,
        source_mode=payload.source_mode,
        user_material=payload.user_material,
        current_level=mission.current_level if mission else None,
        success_criteria=mission.success_criteria if mission else None,
    )

    return MissionPlanResponse(
        mission_id=mission_id,
        selected_sources=curated["selected_sources"],
        rejected_sources=curated["rejected_sources"],
        source_summary=curated["source_summary"],
        recommended_learning_approach=curated["recommended_learning_approach"],
    )
