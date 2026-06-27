from fastapi import APIRouter

from app.agents.lesson_planner import LessonPlannerAgent
from app.agents.resource_curator import ResourceCuratorAgent
from app.models.memory_store import memory_store
from app.schemas.mission_plan import MissionPlanRequest, MissionPlanResponse
from app.schemas.resources import CuratedResource

router = APIRouter()

resource_curator = ResourceCuratorAgent()
lesson_planner = LessonPlannerAgent()

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
    learning_plan = lesson_planner.generate_plan(
        goal=payload.goal,
        current_level=mission.current_level if mission else None,
        success_criteria=mission.success_criteria if mission else None,
        selected_sources=[CuratedResource.model_validate(source) for source in curated["selected_sources"]],
        source_summary=curated["source_summary"],
    )

    return MissionPlanResponse(
        mission_id=mission_id,
        selected_sources=curated["selected_sources"],
        rejected_sources=curated["rejected_sources"],
        source_summary=curated["source_summary"],
        recommended_learning_approach=curated["recommended_learning_approach"],
        mission_type=learning_plan.mission_type,
        objectives=learning_plan.objectives,
        diagnostic_questions=learning_plan.diagnostic_questions,
    )
