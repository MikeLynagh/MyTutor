from dataclasses import dataclass


@dataclass(frozen=True)
class EvalCase:
    name: str
    answer: str
    expected_score_min: float
    expected_score_max: float
    expected_next_task_types: set[str]
    expected_mastery_direction: str


MISSION_PAYLOAD = {
    "goal": "Create and explain a FastAPI GET /health endpoint",
    "why": "Evaluate whether the tutor can teach and assess a concrete backend skill.",
    "success_criteria": 'I can write a FastAPI GET /health route that returns {"status": "ok"} and explain why it is useful.',
    "current_level": "beginner",
    "learning_preference": "step_by_step",
    "source_mode": "web",
}

PLAN_PAYLOAD = {
    "goal": MISSION_PAYLOAD["goal"],
    "source_mode": "web",
    "user_material": "",
}

CASES = [
    EvalCase(
        name="fastapi_health_weak_answer",
        answer="print ok",
        expected_score_min=0.0,
        expected_score_max=0.39,
        expected_next_task_types={"remediation"},
        expected_mastery_direction="decrease_or_small_increase",
    ),
    EvalCase(
        name="fastapi_health_partial_answer",
        answer="FastAPI endpoint",
        expected_score_min=0.4,
        expected_score_max=0.74,
        expected_next_task_types={"new_example"},
        expected_mastery_direction="decrease_or_small_increase",
    ),
    EvalCase(
        name="fastapi_health_strong_answer",
        answer=(
            "The learner can explain the key foundations of creating a FastAPI GET health endpoint clearly. "
            "@app.get('/health') defines the route and returning {'status': 'ok'} lets another system check the API is running."
        ),
        expected_score_min=0.75,
        expected_score_max=1.0,
        expected_next_task_types={"practical_check", "advance"},
        expected_mastery_direction="increase",
    ),
]
