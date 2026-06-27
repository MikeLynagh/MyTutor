from fastapi import APIRouter, HTTPException

from app.agents.lesson_generator import LessonGeneratorAgent
from app.agents.lesson_planner import LessonPlannerAgent
from app.models.memory_store import memory_store
from app.schemas.lesson import LessonStartResponse

router = APIRouter()

lesson_generator = LessonGeneratorAgent()
lesson_planner = LessonPlannerAgent()


@router.post("/missions/{mission_id}/lessons/start", response_model=LessonStartResponse)
def start_lesson(mission_id: str):
    mission = memory_store.get_mission(mission_id)
    if mission is None:
        raise HTTPException(status_code=404, detail="Mission not found")

    mission_plan = memory_store.get_mission_plan(mission_id)
    if mission_plan is None:
        learning_plan = lesson_planner.generate_plan(
            goal=mission.goal,
            current_level=mission.current_level,
            success_criteria=mission.success_criteria,
            selected_sources=[],
            source_summary="",
        )
        objective = learning_plan.objectives[0]
        source_summary = ""
    else:
        objective = mission_plan.objectives[0]
        source_summary = mission_plan.source_summary

    existing_lesson = memory_store.get_lesson(mission_id, objective.id)
    if existing_lesson is not None:
        return LessonStartResponse(mission_id=mission_id, objective_id=objective.id, lesson=existing_lesson)

    lesson = lesson_generator.generate_lesson(
        mission_goal=mission.goal,
        current_level=mission.current_level,
        learning_preference=mission.learning_preference,
        objective=objective,
        source_summary=source_summary,
        recent_errors=[],
    )
    memory_store.save_lesson(mission_id, lesson)
    return LessonStartResponse(mission_id=mission_id, objective_id=objective.id, lesson=lesson)
