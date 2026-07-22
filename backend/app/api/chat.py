import json
import re
from time import perf_counter

from fastapi import APIRouter, HTTPException

from app.models.memory_store import memory_store
from app.schemas.chat import ChatMessage, MissionChatLLMResponse, MissionChatRequest, MissionChatResponse
from app.schemas.lesson import LessonArtifact
from app.schemas.mission_plan import MissionPlanResponse
from app.schemas.plan import Objective
from app.services.event_logger import event_logger
from app.services.llm_client import LLMClient, LLMClientError

router = APIRouter()
llm_client = LLMClient()


@router.post("/missions/{mission_id}/chat", response_model=MissionChatResponse)
def chat_with_mission_tutor(mission_id: str, payload: MissionChatRequest):
    started_at = perf_counter()
    mission = memory_store.get_mission(mission_id)
    if mission is None:
        raise HTTPException(status_code=404, detail="Mission not found")

    mission_plan = memory_store.get_mission_plan(mission_id)
    learner_state = memory_store.get_learner_state(mission_id)
    current_objective = _resolve_current_objective(
        mission_plan=mission_plan,
        current_objective_id=payload.current_objective_id,
        latest_next_task_objective_id=learner_state.latest_next_task.target_objective_id
        if learner_state.latest_next_task is not None
        else None,
    )
    current_lesson = (
        memory_store.get_lesson(mission_id, current_objective.id)
        if current_objective is not None
        else None
    )
    objective_state = (
        memory_store.get_objective_mastery(mission_id, current_objective.id)
        if current_objective is not None
        else None
    )

    system_prompt = (
        "You are a tutor inside an adaptive learning mission. "
        "Answer only using the supplied mission, plan, lesson, learner state, and chat history. "
        "Be concise, practical, and supportive without being chatty. "
        "Prefer explanations, examples, hints, and checks the learner can perform. "
        "Do not browse the web, invent resources, change the mission plan, update mastery, or claim the learner has mastered something. "
        "If the learner asks about something unrelated, briefly redirect them to the current mission. "
        "If the supplied context is insufficient, say what you can answer and what is uncertain."
    )
    user_prompt = json.dumps(
        {
            "message": payload.message,
            "mission": {
                "goal": mission.goal,
                "why": mission.why,
                "success_criteria": mission.success_criteria,
                "current_level": mission.current_level,
                "learning_preference": mission.learning_preference,
                "mission_type": mission.mission_type,
            },
            "plan": _plan_context(mission_plan),
            "current_objective": current_objective.model_dump() if current_objective is not None else None,
            "current_lesson": _lesson_context(current_lesson),
            "learner_state": {
                "current_objective_mastery": objective_state.model_dump() if objective_state is not None else None,
                "latest_next_task": learner_state.latest_next_task.model_dump()
                if learner_state.latest_next_task is not None
                else None,
            },
            "history": [message.model_dump() for message in payload.history[-6:]],
            "response_rules": [
                "Keep the response under 180 words.",
                "Do not provide a full replacement lesson.",
                "When useful, give one concrete example or one next action.",
                "Do not answer unrelated questions as a general assistant.",
            ],
        },
        indent=2,
    )

    try:
        response = llm_client.generate_structured(
            schema=MissionChatLLMResponse,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
    except LLMClientError as exc:
        event_logger.log_event(
            event_type="agent_error",
            mission_id=mission_id,
            objective_id=current_objective.id if current_objective is not None else None,
            lesson_id=current_lesson.lesson_id if current_lesson is not None else None,
            agent_name="MissionTutorChat",
            latency_ms=_elapsed_ms(started_at),
            metadata={"operation": "chat_response", "error": str(exc)[:500]},
        )
        raise HTTPException(status_code=502, detail=f"Tutor chat failed: {exc}") from exc

    event_logger.log_event(
        event_type="chat_response_generated",
        mission_id=mission_id,
        objective_id=current_objective.id if current_objective is not None else None,
        lesson_id=current_lesson.lesson_id if current_lesson is not None else None,
        agent_name="MissionTutorChat",
        latency_ms=_elapsed_ms(started_at),
        metadata={
            "history_count": len(payload.history),
            "message_length": len(payload.message),
            "response_length": len(response.content.strip()),
        },
    )
    return MissionChatResponse(message=ChatMessage(role="assistant", content=response.content.strip()))


def _resolve_current_objective(
    *,
    mission_plan: MissionPlanResponse | None,
    current_objective_id: str | None,
    latest_next_task_objective_id: str | None,
) -> Objective | None:
    if mission_plan is None or not mission_plan.objectives:
        return None

    if current_objective_id:
        for objective in mission_plan.objectives:
            if objective.id == current_objective_id:
                return objective

    if latest_next_task_objective_id:
        for objective in mission_plan.objectives:
            if objective.id == latest_next_task_objective_id:
                return objective

    return mission_plan.objectives[0]


def _plan_context(mission_plan: MissionPlanResponse | None):
    if mission_plan is None:
        return None

    return {
        "mission_type": mission_plan.mission_type,
        "recommended_learning_approach": mission_plan.recommended_learning_approach,
        "objectives": [
            {
                "id": objective.id,
                "title": objective.title,
                "description": objective.description,
                "assessment_type": objective.assessment_type,
                "success_criteria": objective.success_criteria,
                "prerequisites": objective.prerequisites,
            }
            for objective in mission_plan.objectives
        ],
    }


def _lesson_context(lesson: LessonArtifact | None):
    if lesson is None:
        return None

    return {
        "title": lesson.title,
        "objective_id": lesson.objective_id,
        "lesson_text": _truncate(_html_to_text(lesson.lesson_html), 2500),
        "key_points": lesson.key_points[:8],
        "practice_tasks": [practice_task.model_dump() for practice_task in lesson.practice_tasks[:2]],
        "practical_task": lesson.practical_task.model_dump(),
        "assessment": lesson.assessment.model_dump(),
    }


def _html_to_text(html: str) -> str:
    no_tags = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", no_tags).strip()


def _truncate(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value

    return f"{value[:limit].rstrip()}..."


def _elapsed_ms(started_at: float) -> int:
    return round((perf_counter() - started_at) * 1000)
