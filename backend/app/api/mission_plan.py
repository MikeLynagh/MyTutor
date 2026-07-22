from time import perf_counter

from fastapi import APIRouter, HTTPException

from app.agents.lesson_planner import LessonPlannerAgent
from app.agents.resource_curator import ResourceCuratorAgent
from app.models.memory_store import memory_store
from app.schemas.mission_plan import MissionPlanRequest, MissionPlanResponse
from app.schemas.resources import CuratedResource
from app.services.event_logger import event_logger

router = APIRouter()

resource_curator = ResourceCuratorAgent()
lesson_planner = LessonPlannerAgent()


@router.get("/missions/{mission_id}/plan", response_model=MissionPlanResponse)
def get_mission_plan(mission_id: str):
    mission_plan = memory_store.get_mission_plan(mission_id)

    if mission_plan is None:
        raise HTTPException(status_code=404, detail="Mission plan not found")

    return mission_plan


@router.post("/missions/{mission_id}/plan", response_model=MissionPlanResponse)
def create_mission_plan(mission_id: str, payload: MissionPlanRequest):
    started_at = perf_counter()
    mission = memory_store.get_mission(mission_id)
    curated = resource_curator.curate(
        goal=payload.goal,
        source_mode=payload.source_mode,
        user_material=payload.user_material,
        current_level=mission.current_level if mission else None,
        success_criteria=mission.success_criteria if mission else None,
    )
    if resource_curator.last_fallback_used:
        event_logger.log_event(
            event_type="fallback_used",
            mission_id=mission_id,
            agent_name="ResourceCuratorAgent",
            fallback_used=True,
            metadata={
                "operation": "resource_curation",
                "search_error": resource_curator.last_search_error,
            },
        )

    learning_plan = lesson_planner.generate_plan(
        goal=payload.goal,
        current_level=mission.current_level if mission else None,
        success_criteria=mission.success_criteria if mission else None,
        selected_sources=[CuratedResource.model_validate(source) for source in curated["selected_sources"]],
        source_summary=curated["source_summary"],
    )
    if lesson_planner.last_fallback_used:
        event_logger.log_event(
            event_type="fallback_used",
            mission_id=mission_id,
            agent_name="LessonPlannerAgent",
            fallback_used=True,
            metadata={"operation": "lesson_planning"},
        )

    response = MissionPlanResponse(
        mission_id=mission_id,
        selected_sources=curated["selected_sources"],
        rejected_sources=curated["rejected_sources"],
        source_summary=curated["source_summary"],
        recommended_learning_approach=curated["recommended_learning_approach"],
        mission_type=learning_plan.mission_type,
        objectives=learning_plan.objectives,
        diagnostic_questions=learning_plan.diagnostic_questions,
    )
    memory_store.save_mission_plan(mission_id, response)
    event_logger.log_event(
        event_type="plan_created",
        mission_id=mission_id,
        agent_name="ResourceCuratorAgent,LessonPlannerAgent",
        latency_ms=_elapsed_ms(started_at),
        fallback_used=resource_curator.last_fallback_used or lesson_planner.last_fallback_used,
        metadata={
            "source_mode": payload.source_mode,
            "selected_source_count": len(response.selected_sources),
            "rejected_source_count": len(response.rejected_sources),
            "objective_count": len(response.objectives),
            "diagnostic_question_count": len(response.diagnostic_questions),
            "mission_type": response.mission_type,
            "recommended_learning_approach": response.recommended_learning_approach,
        },
    )
    return response


def _elapsed_ms(started_at: float) -> int:
    return round((perf_counter() - started_at) * 1000)
