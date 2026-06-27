import json

from app.schemas.mission import CurrentLevel
from app.schemas.plan import LearningPlan, Objective
from app.schemas.resources import CuratedResource
from app.services.llm_client import LLMClient, LLMClientError


class LessonPlannerAgent:
    def __init__(self, llm_client: LLMClient | None = None):
        self.llm_client = llm_client or LLMClient()

    def generate_plan(
        self,
        goal: str,
        current_level: CurrentLevel | None = None,
        success_criteria: str | None = None,
        selected_sources: list[CuratedResource] | None = None,
        source_summary: str | None = None,
    ) -> LearningPlan:
        normalized_goal = goal.lower()

        if "rubik" in normalized_goal or "cube" in normalized_goal:
            return self._build_rubik_plan()

        llm_plan = self._generate_plan_with_llm(
            goal=goal,
            current_level=current_level,
            success_criteria=success_criteria,
            selected_sources=selected_sources or [],
            source_summary=source_summary or "",
        )
        if llm_plan is not None and self._is_valid_generated_plan(llm_plan):
            return llm_plan

        return self._build_goal_shaped_fallback(goal=goal, normalized_goal=normalized_goal)

    def _build_rubik_plan(self) -> LearningPlan:
        return LearningPlan(
            mission_type="procedural_skill",
            objectives=[
                Objective(
                    id="obj_1",
                    title="Understand cube pieces and notation",
                    description="Learn the difference between centre, edge, and corner pieces and understand basic cube notation.",
                    difficulty=0.1,
                    assessment_type="short_written_answer",
                    prerequisites=[],
                    success_criteria="Learner can identify cube piece types and explain notation such as R, U, F, L, D, and B.",
                ),
                Objective(
                    id="obj_2",
                    title="Solve the white cross",
                    description="Build the white cross while matching edge colours to their corresponding centre pieces.",
                    difficulty=0.2,
                    assessment_type="practical_check",
                    prerequisites=["obj_1"],
                    success_criteria="Learner can solve a correct white cross with matched side colours.",
                ),
                Objective(
                    id="obj_3",
                    title="Solve first-layer corners",
                    description="Insert the white corner pieces to complete the first layer.",
                    difficulty=0.3,
                    assessment_type="practical_check",
                    prerequisites=["obj_2"],
                    success_criteria="Learner can complete the full first layer without disturbing the solved white cross.",
                ),
                Objective(
                    id="obj_4",
                    title="Solve second-layer edges",
                    description="Use the standard beginner method to place the middle-layer edge pieces.",
                    difficulty=0.45,
                    assessment_type="practical_check",
                    prerequisites=["obj_3"],
                    success_criteria="Learner can solve the second layer while preserving the completed first layer.",
                ),
                Objective(
                    id="obj_5",
                    title="Make the yellow cross",
                    description="Recognize top-layer patterns and apply the beginner sequence to form the yellow cross.",
                    difficulty=0.6,
                    assessment_type="practical_check",
                    prerequisites=["obj_4"],
                    success_criteria="Learner can create the yellow cross on the final layer from common beginner states.",
                ),
                Objective(
                    id="obj_6",
                    title="Position the yellow edges",
                    description="Move the yellow edge pieces into the correct locations before solving the corners.",
                    difficulty=0.72,
                    assessment_type="practical_check",
                    prerequisites=["obj_5"],
                    success_criteria="Learner can place all yellow edges in the correct positions.",
                ),
                Objective(
                    id="obj_7",
                    title="Position the yellow corners",
                    description="Identify which yellow corner pieces belong in each location and position them correctly.",
                    difficulty=0.84,
                    assessment_type="practical_check",
                    prerequisites=["obj_6"],
                    success_criteria="Learner can place yellow corner pieces into the correct slots before final orientation.",
                ),
                Objective(
                    id="obj_8",
                    title="Orient the yellow corners and finish the cube",
                    description="Use the final beginner sequence to orient the last-layer corners and complete the solve.",
                    difficulty=1.0,
                    assessment_type="practical_check",
                    prerequisites=["obj_7"],
                    success_criteria="Learner can finish the cube from a last-layer corner orientation state without external help.",
                ),
            ],
            diagnostic_questions=[
                "Have you ever solved one full face of a Rubik's cube before?",
                "Do you already know what the moves R, U, F, L, D, and B mean?",
                "Can you identify an edge piece and a corner piece on a physical cube?",
            ],
        )

    def _build_goal_shaped_fallback(self, goal: str, normalized_goal: str) -> LearningPlan:
        topic = goal.strip() or "this topic"
        return LearningPlan(
            mission_type=self._infer_mission_type(normalized_goal),
            objectives=[
                Objective(
                    id="obj_1",
                    title=f"Learn the foundations of {topic}",
                    description=f"Build a beginner-friendly understanding of the core ideas, terms, and first steps involved in {topic}.",
                    difficulty=0.2,
                    assessment_type="short_written_answer",
                    prerequisites=[],
                    success_criteria=f"Learner can explain the basic concepts and initial workflow for {topic} in simple terms.",
                ),
                Objective(
                    id="obj_2",
                    title=f"Practice a guided example in {topic}",
                    description=f"Work through a structured example or exercise that demonstrates how {topic} is applied in practice.",
                    difficulty=0.55,
                    assessment_type="practical_check",
                    prerequisites=["obj_1"],
                    success_criteria=f"Learner can follow a guided example in {topic} and describe what each step is doing.",
                ),
                Objective(
                    id="obj_3",
                    title=f"Apply {topic} independently",
                    description=f"Use the learned process to complete a small independent task related to {topic}.",
                    difficulty=0.85,
                    assessment_type="practical_check",
                    prerequisites=["obj_2"],
                    success_criteria=f"Learner can complete a small independent task in {topic} with minimal prompting.",
                ),
            ],
            diagnostic_questions=[
                f"What experience do you already have with {topic}?",
                f"What part of {topic} feels most confusing or unfamiliar right now?",
                f"What would a successful first practical win in {topic} look like for you?",
            ],
        )

    def _generate_plan_with_llm(
        self,
        *,
        goal: str,
        current_level: CurrentLevel | None,
        success_criteria: str | None,
        selected_sources: list[CuratedResource],
        source_summary: str,
    ) -> LearningPlan | None:
        system_prompt = (
            "You are a lesson planner for a learning mission. "
            "Return a sequenced beginner-appropriate learning plan in valid json only. "
            "Use the provided schema exactly. "
            "Do not invent extra fields. "
            "Make prerequisites explicit and keep objective difficulty as a normalized progression hint between 0 and 1."
        )
        user_prompt = json.dumps(
            {
                "mission_goal": goal,
                "current_level": current_level or "beginner",
                "success_criteria": success_criteria or "",
                "source_summary": source_summary,
                "selected_sources": [
                    {
                        "title": source.title,
                        "url": source.url,
                        "reason": source.reason,
                        "type": source.type,
                    }
                    for source in selected_sources[:5]
                ],
                "requirements": {
                    "minimum_objectives": 3,
                    "objective_fields": [
                        "id",
                        "title",
                        "description",
                        "difficulty",
                        "assessment_type",
                        "prerequisites",
                        "success_criteria",
                    ],
                    "diagnostic_questions_required": True,
                    "allowed_assessment_types": [
                        "short_written_answer",
                        "multiple_choice",
                        "practical_check",
                        "free_form",
                    ],
                },
            },
            indent=2,
        )

        try:
            return self.llm_client.generate_structured(
                schema=LearningPlan,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
        except LLMClientError:
            return None

    def _is_valid_generated_plan(self, plan: LearningPlan) -> bool:
        if len(plan.objectives) < 3:
            return False

        if not plan.diagnostic_questions or any(not question.strip() for question in plan.diagnostic_questions):
            return False

        objective_ids = [objective.id for objective in plan.objectives]
        if len(objective_ids) != len(set(objective_ids)):
            return False

        valid_ids = set(objective_ids)
        seen_titles: set[str] = set()

        for index, objective in enumerate(plan.objectives):
            normalized_title = objective.title.strip().lower()
            if not normalized_title or normalized_title in seen_titles:
                return False
            seen_titles.add(normalized_title)

            if not objective.description.strip() or not objective.success_criteria.strip():
                return False

            if objective.id in objective.prerequisites:
                return False

            if any(prerequisite not in valid_ids for prerequisite in objective.prerequisites):
                return False

            prior_ids = {prior_objective.id for prior_objective in plan.objectives[:index]}
            if any(prerequisite not in prior_ids for prerequisite in objective.prerequisites):
                return False

        return True

    def _infer_mission_type(self, normalized_goal: str):
        if any(keyword in normalized_goal for keyword in ["build", "code", "program", "api", "backend", "frontend", "python"]):
            return "technical_skill"

        if any(keyword in normalized_goal for keyword in ["learn", "play", "cook", "draw", "write", "speak"]):
            return "procedural_skill"

        return "conceptual_topic"
