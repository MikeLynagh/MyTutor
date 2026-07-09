from fastapi import APIRouter, HTTPException

from app.agents.lesson_generator import LessonGeneratorAgent
from app.agents.lesson_planner import LessonPlannerAgent
from app.models.memory_store import memory_store
from app.schemas.lesson import LessonStartResponse, NextTaskResponse
from app.schemas.mastery import NextLearningTask
from app.schemas.mission_plan import MissionPlanResponse
from app.schemas.plan import Objective

router = APIRouter()

lesson_generator = LessonGeneratorAgent()
lesson_planner = LessonPlannerAgent()


@router.post("/missions/{mission_id}/lessons/start", response_model=LessonStartResponse)
def start_lesson(mission_id: str, force: bool = False):
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
        mission_plan = MissionPlanResponse(
            mission_id=mission_id,
            selected_sources=[],
            rejected_sources=[],
            source_summary="",
            recommended_learning_approach="guided_foundations",
            mission_type=learning_plan.mission_type,
            objectives=learning_plan.objectives,
            diagnostic_questions=learning_plan.diagnostic_questions,
        )
        memory_store.save_mission_plan(mission_id, mission_plan)
        objective = learning_plan.objectives[0]
        source_summary = ""
    else:
        objective = mission_plan.objectives[0]
        source_summary = mission_plan.source_summary

    existing_lesson = memory_store.get_lesson(mission_id, objective.id)
    if existing_lesson is not None and not force:
        return LessonStartResponse(mission_id=mission_id, objective_id=objective.id, lesson=existing_lesson)

    lesson = lesson_generator.generate_lesson(
        mission_goal=mission.goal,
        current_level=mission.current_level,
        learning_preference=mission.learning_preference,
        objective=objective,
        source_summary=source_summary,
        selected_sources=mission_plan.selected_sources,
        recent_errors=[],
    )
    memory_store.save_lesson(mission_id, lesson)
    return LessonStartResponse(mission_id=mission_id, objective_id=objective.id, lesson=lesson)


@router.post("/missions/{mission_id}/tasks/next", response_model=NextTaskResponse)
def next_task(mission_id: str):
    mission = memory_store.get_mission(mission_id)
    if mission is None:
        raise HTTPException(status_code=404, detail="Mission not found")

    mission_plan = memory_store.get_mission_plan(mission_id)
    if mission_plan is None:
        raise HTTPException(status_code=404, detail="Mission plan not found")

    latest_next_task = memory_store.get_latest_next_task(mission_id)
    if latest_next_task is None:
        raise HTTPException(status_code=400, detail="No next task available. Submit an answer first.")

    objective = resolve_next_task_objective(
        mission_plan=mission_plan,
        next_task=latest_next_task,
    )
    objective_state = memory_store.get_objective_mastery(
        mission_id=mission_id,
        objective_id=objective.id,
    )

    existing_lesson = memory_store.get_lesson(mission_id, objective.id)
    if latest_next_task.type == "advance" and existing_lesson is not None:
        return NextTaskResponse(
            mission_id=mission_id,
            objective_id=objective.id,
            task_type=latest_next_task.type,
            lesson=existing_lesson,
        )

    lesson = lesson_generator.generate_lesson(
        mission_goal=mission.goal,
        current_level=mission.current_level,
        learning_preference=mission.learning_preference,
        objective=objective,
        source_summary=mission_plan.source_summary,
        selected_sources=mission_plan.selected_sources,
        recent_errors=objective_state.recent_errors,
    )
    memory_store.save_lesson(mission_id, lesson)
    return NextTaskResponse(
        mission_id=mission_id,
        objective_id=objective.id,
        task_type=latest_next_task.type,
        lesson=lesson,
    )


def resolve_next_task_objective(
    *,
    mission_plan: MissionPlanResponse,
    next_task: NextLearningTask,
) -> Objective:
    current_index = next(
        (
            index
            for index, objective in enumerate(mission_plan.objectives)
            if objective.id == next_task.target_objective_id
        ),
        None,
    )
    if current_index is None:
        raise HTTPException(status_code=404, detail="Target objective not found in mission plan")

    if next_task.type != "advance":
        return mission_plan.objectives[current_index]

    next_index = current_index + 1
    if next_index >= len(mission_plan.objectives):
        return mission_plan.objectives[current_index]

    return mission_plan.objectives[next_index]
