import json
import logging
from uuid import uuid4

from app.schemas.lesson import Assessment, LessonArtifact, PracticalTask
from app.schemas.mission import CurrentLevel, LearningPreference
from app.schemas.plan import Objective
from app.services.lesson_sanitizer import LessonSanitizer
from app.services.llm_client import LLMClient, LLMClientError

logger = logging.getLogger(__name__)


class LessonGeneratorAgent:
    def __init__(self, llm_client: LLMClient | None = None, sanitizer: LessonSanitizer | None = None):
        self.llm_client = llm_client or LLMClient()
        self.sanitizer = sanitizer or LessonSanitizer()

    def generate_lesson(
        self,
        *,
        mission_goal: str,
        current_level: CurrentLevel | None,
        learning_preference: LearningPreference | None,
        objective: Objective,
        source_summary: str,
        recent_errors: list[str] | None = None,
    ) -> LessonArtifact:
        lesson_id = str(uuid4())
        generated = self._generate_with_llm(
            mission_goal=mission_goal,
            current_level=current_level,
            learning_preference=learning_preference,
            objective=objective,
            source_summary=source_summary,
            recent_errors=recent_errors or [],
        )

        if generated is not None:
            generated.lesson_id = lesson_id
            generated.lesson_html = self.sanitizer.sanitize(generated.lesson_html)
            if self._is_valid_lesson(generated):
                return generated
            logger.warning("LLM lesson output failed validation for objective %s", objective.id)

        fallback = self._build_fallback_lesson(
            lesson_id=lesson_id,
            mission_goal=mission_goal,
            objective=objective,
            recent_errors=recent_errors or [],
        )
        fallback.lesson_html = self.sanitizer.sanitize(fallback.lesson_html)
        return fallback

    def _generate_with_llm(
        self,
        *,
        mission_goal: str,
        current_level: CurrentLevel | None,
        learning_preference: LearningPreference | None,
        objective: Objective,
        source_summary: str,
        recent_errors: list[str],
    ) -> LessonArtifact | None:
        system_prompt = (
            "You are a lesson generator for a learning mission. "
            "Use only the supplied objective and context. "
            "Do not change the objective. "
            "Return valid json only and follow the schema exactly. "
            "Keep the lesson concise, stepwise, and aligned to the assessment."
        )
        user_prompt = json.dumps(
            {
                "mission_goal": mission_goal,
                "current_level": current_level or "beginner",
                "learning_preference": learning_preference or "step_by_step",
                "objective": objective.model_dump(),
                "source_summary": source_summary,
                "recent_errors": recent_errors,
                "requirements": {
                    "lesson_html_tags": [
                        "article",
                        "section",
                        "h2",
                        "h3",
                        "p",
                        "ul",
                        "ol",
                        "li",
                        "strong",
                        "em",
                        "code",
                        "pre",
                        "blockquote",
                    ],
                    "practical_task_required": True,
                    "assessment_alignment_required": True,
                    "one_concrete_example_max": True,
                },
            },
            indent=2,
        )

        try:
            return self.llm_client.generate_structured(
                schema=LessonArtifact,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
        except LLMClientError as exc:
            logger.warning("LLM lesson generation failed: %s", exc)
            return None

    def _build_fallback_lesson(
        self,
        *,
        lesson_id: str,
        mission_goal: str,
        objective: Objective,
        recent_errors: list[str],
    ) -> LessonArtifact:
        normalized_goal = mission_goal.lower()
        if self._is_rubik_mission(normalized_goal):
            return self._build_rubik_objective_one_fallback(lesson_id=lesson_id, objective=objective, recent_errors=recent_errors)

        lesson_html = (
            "<article>"
            f"<h2>{escape_text(objective.title)}</h2>"
            f"<p>{escape_text(objective.description)}</p>"
            "<section>"
            "<h3>Key idea</h3>"
            f"<p>{escape_text(objective.success_criteria)}</p>"
            "</section>"
            "<section>"
            "<h3>Practice</h3>"
            f"<p>Work through a small guided example related to {escape_text(mission_goal)}.</p>"
            "</section>"
            "</article>"
        )
        return LessonArtifact(
            lesson_id=lesson_id,
            objective_id=objective.id,
            title=objective.title,
            lesson_html=lesson_html,
            key_points=[
                objective.description,
                objective.success_criteria,
                "Use the practice task to confirm you understand the first step.",
            ],
            practical_task=PracticalTask(
                instruction=f"Try a small guided exercise related to {mission_goal}.",
                success_criteria=objective.success_criteria,
            ),
            assessment=Assessment(
                type=objective.assessment_type,
                question=f"Explain or demonstrate the core idea behind {objective.title}.",
                expected_answer=objective.success_criteria,
                rubric=[
                    "Addresses the core idea",
                    "Matches the objective success criteria",
                    "Shows learner can apply the idea",
                ],
            ),
        )

    def _build_rubik_objective_one_fallback(
        self,
        *,
        lesson_id: str,
        objective: Objective,
        recent_errors: list[str],
    ) -> LessonArtifact:
        lesson_html = (
            "<article>"
            "<h2>Cube pieces and notation</h2>"
            "<section>"
            "<h3>What you need to know</h3>"
            "<p>Centres have one colour, edges have two colours, and corners have three colours.</p>"
            "</section>"
            "<section>"
            "<h3>Notation</h3>"
            "<p>R, U, F, L, D, and B describe common cube moves.</p>"
            "</section>"
            "<section>"
            "<h3>Practice</h3>"
            "<p>Pick up your cube and identify four edge pieces and four corner pieces.</p>"
            "</section>"
            "</article>"
        )
        return LessonArtifact(
            lesson_id=lesson_id,
            objective_id=objective.id,
            title="Cube pieces and notation",
            lesson_html=lesson_html,
            key_points=[
                "Centre pieces have one colour.",
                "Edge pieces have two colours.",
                "Corner pieces have three colours.",
            ],
            practical_task=PracticalTask(
                instruction="Pick up your cube and identify four edge pieces and four corner pieces.",
                success_criteria="The learner can correctly distinguish centre, edge, and corner pieces.",
            ),
            assessment=Assessment(
                type="short_written_answer",
                question="Explain the difference between centre, edge, and corner pieces in your own words.",
                expected_answer="Centres have one colour, edges have two colours, and corners have three colours.",
                rubric=[
                    "Mentions centres have one colour",
                    "Mentions edges have two colours",
                    "Mentions corners have three colours",
                ],
            ),
        )

    def _is_rubik_mission(self, normalized_goal: str) -> bool:
        rubik_indicators = [
            "rubik",
            "rubik's cube",
            "rubiks cube",
            "3x3 cube",
            "solve the cube",
            "speedcube",
            "speedcubing",
        ]
        return any(indicator in normalized_goal for indicator in rubik_indicators)

    def _is_valid_lesson(self, lesson: LessonArtifact) -> bool:
        if not lesson.lesson_id.strip() or not lesson.objective_id.strip() or not lesson.title.strip():
            return False

        if not lesson.lesson_html.strip():
            return False

        if len(lesson.key_points) < 3:
            return False

        if not lesson.practical_task or not lesson.practical_task.instruction.strip() or not lesson.practical_task.success_criteria.strip():
            return False

        if not lesson.assessment.question.strip() or not lesson.assessment.rubric:
            return False

        if lesson.assessment.type == "short_written_answer" and not lesson.assessment.expected_answer:
            return False

        return True


def escape_text(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )
