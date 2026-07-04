from fastapi import APIRouter, HTTPException

from app.agents.evaluator import EvaluatorAgent
from app.models.memory_store import memory_store
from app.schemas.answer import AnswerEvaluationWithMasteryResponse, AnswerSubmission
from app.services.mastery_tracker import MasteryTracker

router = APIRouter()
evaluator = EvaluatorAgent()
mastery_tracker = MasteryTracker()


@router.post("/missions/{mission_id}/answers", response_model=AnswerEvaluationWithMasteryResponse)
def submit_answer(mission_id: str, payload: AnswerSubmission):
    mission = memory_store.get_mission(mission_id)
    if mission is None:
        raise HTTPException(status_code=404, detail="Mission not found")

    lesson = memory_store.get_lesson(mission_id, payload.objective_id)
    if lesson is None or lesson.lesson_id != payload.lesson_id:
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

    evaluation = evaluator.evaluate_answer(
        objective=objective,
        assessment=lesson.assessment,
        learner_answer=payload.answer,
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

    return AnswerEvaluationWithMasteryResponse(
        evaluation=evaluation,
        mastery=mastery,
    )
