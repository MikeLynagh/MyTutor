from app.schemas.mastery import NextLearningTask
from app.schemas.mission import MissionType
from app.schemas.plan import AssessmentType


class TaskRouter:
    def __init__(
        self,
        *,
        low_score_threshold: float = 0.4,
        correct_threshold: float = 0.75,
        advance_mastery_threshold: float = 0.7,
    ) -> None:
        self.low_score_threshold = low_score_threshold
        self.correct_threshold = correct_threshold
        self.advance_mastery_threshold = advance_mastery_threshold

    def route(
        self,
        *,
        objective_id: str,
        objective_title: str,
        success_criteria: str,
        assessment_type: AssessmentType,
        mission_type: MissionType,
        score: float,
        mastery_after: float,
        misconception: str | None,
    ) -> NextLearningTask:
        if score < self.low_score_threshold:
            return self._remediation_task(
                objective_id=objective_id,
                objective_title=objective_title,
                success_criteria=success_criteria,
                misconception=misconception,
            )

        if score < self.correct_threshold:
            return self._new_example_task(
                objective_id=objective_id,
                objective_title=objective_title,
                success_criteria=success_criteria,
                misconception=misconception,
            )

        if mastery_after >= self.advance_mastery_threshold:
            return self._advance_task(
                objective_id=objective_id,
                success_criteria=success_criteria,
            )

        if self._needs_practical_check(
            assessment_type=assessment_type,
            mission_type=mission_type,
        ):
            return self._practical_check_task(
                objective_id=objective_id,
                objective_title=objective_title,
                success_criteria=success_criteria,
            )

        return self._retrieval_check_task(
            objective_id=objective_id,
            objective_title=objective_title,
            success_criteria=success_criteria,
        )

    def _needs_practical_check(
        self,
        *,
        assessment_type: AssessmentType,
        mission_type: MissionType,
    ) -> bool:
        return (
            assessment_type == "short_written_answer"
            and mission_type in {"procedural_skill", "technical_skill"}
        )

    def _remediation_task(
        self,
        *,
        objective_id: str,
        objective_title: str,
        success_criteria: str,
        misconception: str | None,
    ) -> NextLearningTask:
        focus = misconception or success_criteria
        return NextLearningTask(
            type="remediation",
            title=f"Review {objective_title}",
            reason="Your answer suggests this idea needs a clearer explanation before more practice.",
            instruction=f"Review the key idea for {objective_title}. Focus on: {focus}",
            success_criteria=success_criteria,
            response_type="short_written_answer",
            target_objective_id=objective_id,
        )

    def _new_example_task(
        self,
        *,
        objective_id: str,
        objective_title: str,
        success_criteria: str,
        misconception: str | None,
    ) -> NextLearningTask:
        focus = misconception or success_criteria
        return NextLearningTask(
            type="new_example",
            title=f"Try another example for {objective_title}",
            reason="You are partly there, but another example should help make the pattern more reliable.",
            instruction=f"Work through a new example for {objective_title}. Pay attention to: {focus}",
            success_criteria=success_criteria,
            response_type="short_written_answer",
            target_objective_id=objective_id,
        )

    def _practical_check_task(
        self,
        *,
        objective_id: str,
        objective_title: str,
        success_criteria: str,
    ) -> NextLearningTask:
        return NextLearningTask(
            type="practical_check",
            title=f"Apply {objective_title}",
            reason="You explained the idea well, but this objective needs evidence that you can apply it.",
            instruction=f"Do a small practical check for {objective_title}. Then briefly describe what you did.",
            success_criteria=success_criteria,
            response_type="short_written_answer",
            target_objective_id=objective_id,
        )

    def _retrieval_check_task(
        self,
        *,
        objective_id: str,
        objective_title: str,
        success_criteria: str,
    ) -> NextLearningTask:
        return NextLearningTask(
            type="retrieval_check",
            title=f"Recall {objective_title}",
            reason="You gave a strong answer. A quick retrieval check will help strengthen retention.",
            instruction=f"Without looking back at the lesson, explain the key idea behind {objective_title}.",
            success_criteria=success_criteria,
            response_type="short_written_answer",
            target_objective_id=objective_id,
        )

    def _advance_task(
        self,
        *,
        objective_id: str,
        success_criteria: str,
    ) -> NextLearningTask:
        return NextLearningTask(
            type="advance",
            title="Move to the next objective",
            reason="Your answer and mastery estimate suggest you are ready for the next objective.",
            instruction="Continue to the next objective in your mission plan.",
            success_criteria=success_criteria,
            response_type="none",
            target_objective_id=objective_id,
        )
