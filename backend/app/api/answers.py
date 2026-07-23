from time import perf_counter

from fastapi import APIRouter, HTTPException

from app.agents.evaluator import EvaluatorAgent
from app.models.memory_store import memory_store
from app.schemas.answer import AnswerEvaluationWithMasteryResponse, AnswerSubmission
from app.services.event_logger import event_logger
from app.services.mastery_tracker import MasteryTracker
from app.services.task_router import TaskRouter

router = APIRouter()
evaluator = EvaluatorAgent()
mastery_tracker = MasteryTracker()
task_router = TaskRouter()


@router.post("/missions/{mission_id}/answers", response_model=AnswerEvaluationWithMasteryResponse)
def submit_answer(mission_id: str, payload: AnswerSubmission):
    started_at = perf_counter()
    mission = memory_store.get_mission(mission_id)
    if mission is None:
        raise HTTPException(status_code=404, detail="Mission not found")

    lesson = memory_store.get_lesson(mission_id, payload.objective_id)
    if lesson is None or lesson.lesson_id != payload.lesson_id:
        lesson = memory_store.get_lesson_by_id(mission_id, payload.lesson_id)

    if lesson is None or lesson.objective_id != payload.objective_id:
        raise HTTPException(status_code=404, detail="Lesson not found for this mission and objective")

    mission_plan = memory_store.get_mission_plan(mission_id)
    if mission_plan is None:
        raise HTTPException(status_code=404, detail="Mission plan not found")

    objective = next(
        (candidate for candidate in mission_plan.objectives if candidate.id == payload.objective_id),
        None,
    )
    if objective is None:
        raise HTTPException(status_code=404, detail="Objective not found in mission plan")

    event_logger.log_event(
        event_type="answer_submitted",
        mission_id=mission_id,
        objective_id=payload.objective_id,
        lesson_id=payload.lesson_id,
        metadata={
            "answer_length": len(payload.answer),
            "assessment_type": lesson.assessment.type,
        },
    )

    evaluation_started_at = perf_counter()
    evaluation = evaluator.evaluate_answer(
        objective=objective,
        assessment=lesson.assessment,
        learner_answer=payload.answer,
    )
    event_logger.log_event(
        event_type="evaluation_completed",
        mission_id=mission_id,
        objective_id=payload.objective_id,
        lesson_id=payload.lesson_id,
        agent_name="EvaluatorAgent",
        score=evaluation.score,
        latency_ms=_elapsed_ms(evaluation_started_at),
        fallback_used=evaluator.last_fallback_used,
        metadata={
            "is_correct": evaluation.is_correct,
            "missing_point_count": len(evaluation.missing_points),
            "has_misconception": evaluation.misconception is not None,
        },
    )
    if evaluator.last_fallback_used:
        event_logger.log_event(
            event_type="fallback_used",
            mission_id=mission_id,
            objective_id=payload.objective_id,
            lesson_id=payload.lesson_id,
            agent_name="EvaluatorAgent",
            fallback_used=True,
            metadata={"operation": "answer_evaluation"},
        )

    objective_state = memory_store.get_objective_mastery(
        mission_id=mission_id,
        objective_id=payload.objective_id,
    )

    mastery = mastery_tracker.update(
        objective_id=payload.objective_id,
        current_mastery=objective_state.p_mastery,
        score=evaluation.score,
    )

    objective_state.p_mastery = mastery.mastery_after
    objective_state.attempts += 1
    objective_state.last_feedback = evaluation.feedback
    objective_state.recent_errors = [
        error
        for error in [
            evaluation.misconception,
            *evaluation.missing_points,
        ]
        if error
    ][-5:]
    memory_store.save_objective_mastery(
        mission_id=mission_id,
        objective_state=objective_state,
    )
    event_logger.log_event(
        event_type="mastery_updated",
        mission_id=mission_id,
        objective_id=payload.objective_id,
        lesson_id=payload.lesson_id,
        score=evaluation.score,
        mastery_before=mastery.mastery_before,
        mastery_after=mastery.mastery_after,
        metadata={
            "attempts": objective_state.attempts,
            "recent_error_count": len(objective_state.recent_errors),
        },
    )

    next_task = task_router.route(
        objective_id=objective.id,
        objective_title=objective.title,
        success_criteria=objective.success_criteria,
        assessment_type=objective.assessment_type,
        mission_type=mission_plan.mission_type,
        score=evaluation.score,
        mastery_after=mastery.mastery_after,
        misconception=evaluation.misconception,
    )

    memory_store.save_latest_next_task(
        mission_id=mission_id,
        next_task=next_task,
    )
    event_logger.log_event(
        event_type="next_task_selected",
        mission_id=mission_id,
        objective_id=objective.id,
        lesson_id=payload.lesson_id,
        score=evaluation.score,
        mastery_before=mastery.mastery_before,
        mastery_after=mastery.mastery_after,
        next_task_type=next_task.type,
        latency_ms=_elapsed_ms(started_at),
        metadata={
            "response_type": next_task.response_type,
            "target_objective_id": next_task.target_objective_id,
        },
    )

    memory_store.save_answer_evaluation(
        mission_id=mission_id,
        submission=payload,
        evaluation=evaluation,
        mastery=mastery,
        next_task=next_task,
    )

    return AnswerEvaluationWithMasteryResponse(
        evaluation=evaluation,
        mastery=mastery,
        next_task=next_task,
    )


def _elapsed_ms(started_at: float) -> int:
    return round((perf_counter() - started_at) * 1000)
