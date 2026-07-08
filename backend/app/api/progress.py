from fastapi import APIRouter, HTTPException

from app.models.memory_store import memory_store
from app.models.learner import ObjectiveMasteryState
from app.schemas.progress import MissionProgressResponse, ObjectiveProgress, ObjectiveProgressStatus

router = APIRouter()

MASTERY_THRESHOLD = 0.7


@router.get("/missions/{mission_id}/progress", response_model=MissionProgressResponse)
def get_mission_progress(mission_id: str):
    mission = memory_store.get_mission(mission_id)
    if mission is None:
        raise HTTPException(status_code=404, detail="Mission not found")

    mission_plan = memory_store.get_mission_plan(mission_id)
    if mission_plan is None:
        raise HTTPException(status_code=404, detail="Mission plan not found")

    learner_state = memory_store.get_learner_state(mission_id)
    objective_progress = []

    for objective in mission_plan.objectives:
        objective_state = learner_state.objectives.get(objective.id) or ObjectiveMasteryState(
            objective_id=objective.id
        )
        objective_progress.append(
            ObjectiveProgress(
                objective_id=objective.id,
                title=objective.title,
                description=objective.description,
                assessment_type=objective.assessment_type,
                success_criteria=objective.success_criteria,
                mastery=objective_state.p_mastery,
                attempts=objective_state.attempts,
                status=_objective_status(objective_state),
                recent_errors=objective_state.recent_errors,
                last_feedback=objective_state.last_feedback,
            )
        )

    overall_mastery = (
        sum(objective.mastery for objective in objective_progress) / len(objective_progress)
        if objective_progress
        else 0.0
    )

    return MissionProgressResponse(
        mission_id=mission_id,
        overall_mastery=overall_mastery,
        current_next_task=learner_state.latest_next_task,
        objectives=objective_progress,
    )


def _objective_status(objective_state: ObjectiveMasteryState) -> ObjectiveProgressStatus:
    if objective_state.p_mastery >= MASTERY_THRESHOLD:
        return "mastered"

    if objective_state.attempts > 0:
        return "in_progress"

    return "not_started"
