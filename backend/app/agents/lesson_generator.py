import json
import logging
from uuid import uuid4

from app.schemas.lesson import Assessment, LessonArtifact, PracticalTask, PracticeTask
from app.schemas.mission import CurrentLevel, LearningPreference
from app.schemas.plan import Objective
from app.schemas.resources import CuratedResource
from app.services.lesson_sanitizer import LessonSanitizer
from app.services.llm_client import LLMClient, LLMClientError

logger = logging.getLogger(__name__)


class LessonGeneratorAgent:
    def __init__(self, llm_client: LLMClient | None = None, sanitizer: LessonSanitizer | None = None):
        self.llm_client = llm_client or LLMClient()
        self.sanitizer = sanitizer or LessonSanitizer()
        self.last_fallback_used = False

    def generate_lesson(
        self,
        *,
        mission_goal: str,
        current_level: CurrentLevel | None,
        learning_preference: LearningPreference | None,
        objective: Objective,
        source_summary: str,
        selected_sources: list[CuratedResource] | None = None,
        recent_errors: list[str] | None = None,
    ) -> LessonArtifact:
        self.last_fallback_used = False
        lesson_id = str(uuid4())
        generated = self._generate_with_llm(
            mission_goal=mission_goal,
            current_level=current_level,
            learning_preference=learning_preference,
            objective=objective,
            source_summary=source_summary,
            selected_sources=selected_sources or [],
            recent_errors=recent_errors or [],
        )

        if generated is not None:
            generated.lesson_id = lesson_id
            generated.lesson_html = self.sanitizer.sanitize(generated.lesson_html)
            generated.practice_tasks = self._normalise_practice_tasks(generated, objective)
            validation_errors = self._lesson_validation_errors(generated)
            if not validation_errors:
                return generated
            logger.warning(
                "LLM lesson output failed validation for objective %s: %s",
                objective.id,
                ", ".join(validation_errors),
            )

        self.last_fallback_used = True
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
        selected_sources: list[CuratedResource],
        recent_errors: list[str],
    ) -> LessonArtifact | None:
        system_prompt = (
            "You are a lesson generator for a learning mission. "
            "Use only the supplied objective and context. "
            "Do not change the objective. "
            "Return valid json only and follow the schema exactly. "
            "Keep the lesson concise, stepwise, and aligned to the assessment. "
            "Teach one small idea at a time, then give two short practice tasks before the final assessment. "
            "Use source highlights as grounding when they are relevant, but do not copy long passages. "
            "Use safe semantic HTML to reduce cognitive load when useful. "
            "Every full lesson must include one useful visual teaching structure in lesson_html. "
            "Choose the structure based on the objective: use a table for comparisons, an ordered sequence for workflows, "
            "a code block for software examples, a flowchart-style text diagram for systems, or a worked example for applied concepts. "
            "Visual structure should clarify comparisons, sequences, examples, checks, diagrams, tables, or callouts. "
            "Do not add decorative visuals."
        )
        user_prompt = json.dumps(
            {
                "mission_goal": mission_goal,
                "current_level": current_level or "beginner",
                "learning_preference": learning_preference or "step_by_step",
                "objective": objective.model_dump(),
                "source_summary": source_summary,
                "source_evidence": [
                    {
                        "title": source.title,
                        "url": source.url,
                        "highlights": source.highlights[:2],
                    }
                    for source in selected_sources[:3]
                ],
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
                        "figure",
                        "figcaption",
                        "table",
                        "thead",
                        "tbody",
                        "tr",
                        "th",
                        "td",
                        "hr",
                        "div",
                        "span",
                    ],
                    "allowed_css_classes": [
                        "lesson-callout",
                        "lesson-example",
                        "lesson-check",
                        "lesson-sequence",
                        "lesson-comparison",
                        "lesson-diagram",
                        "lesson-muted",
                        "lesson-label",
                    ],
                    "visual_patterns": [
                        "comparison",
                        "step_sequence",
                        "checklist",
                        "table",
                        "callout",
                        "worked_example",
                        "flowchart_style_text_diagram",
                        "code_block",
                    ],
                    "visual_structure_required": {
                        "count": "at_least_one",
                        "purpose": "clarify the concept, workflow, decision, system relationship, example, or assessment target",
                        "allowed_forms": [
                            "table",
                            "ordered sequence",
                            "code block",
                            "flowchart-style text diagram using safe HTML or preformatted text",
                            "worked example",
                            "comparison block",
                        ],
                        "do_not_use": [
                            "decorative graphics",
                            "empty diagram placeholders",
                            "visuals that repeat the same text without adding structure",
                        ],
                    },
                    "practical_task_required": True,
                    "practice_tasks_required": {
                        "count": 2,
                        "practice_1": "Directly apply the lesson idea in a low-friction way.",
                        "practice_2": "Apply the same idea with changed surface details or a slightly harder variation.",
                        "constraints": [
                            "Keep each practice prompt short.",
                            "Make each task answerable without hidden context.",
                            "Avoid trivia unless the objective is explicitly about memorising facts.",
                            "Use code, commands, examples, or concrete actions when they fit the topic.",
                        ],
                    },
                    "assessment_alignment_required": True,
                    "one_concrete_example_max": True,
                    "do_not_include": [
                        "script",
                        "iframe",
                        "style",
                        "form",
                        "input",
                        "button",
                        "event_handlers",
                        "external_embeds",
                        "decorative_images",
                    ],
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

        safe_title = escape_text(objective.title)
        safe_description = escape_text(objective.description)
        safe_success_criteria = escape_text(objective.success_criteria)
        safe_goal = escape_text(mission_goal)
        lesson_html = (
            "<article>"
            f"<h2>{safe_title}</h2>"
            "<section>"
            "<h3>Plain-English explanation</h3>"
            f"<p>{safe_description}</p>"
            f"<p>The goal is to make this idea usable: {safe_success_criteria}</p>"
            "</section>"
            "<section>"
            "<h3>Why it matters</h3>"
            f"<p>This step supports your mission to {safe_goal}. It gives you one concrete capability to practise before moving on.</p>"
            "</section>"
            "<section class=\"lesson-example\">"
            "<h3>Concrete example</h3>"
            f"<p>Take a small example connected to <strong>{safe_title}</strong>. First identify the input or situation, then apply the key idea, then check whether the result meets the success criteria.</p>"
            "</section>"
            "<section class=\"lesson-sequence\">"
            "<h3>Use this sequence</h3>"
            "<ol>"
            "<li>State the idea in one sentence.</li>"
            "<li>Apply it to one simple example.</li>"
            "<li>Check the result against the success criteria.</li>"
            "<li>Explain what would change in a slightly different example.</li>"
            "</ol>"
            "</section>"
            "<section class=\"lesson-callout\">"
            "<h3>Common mistake</h3>"
            "<p>Do not stop at recognition. A good answer should show that you can apply the idea, not only name it.</p>"
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
            practice_tasks=[
                PracticeTask(
                    id="practice_1",
                    prompt=f"Apply {objective.title} to one simple example and compare the result with the success criteria.",
                    purpose="direct_application",
                    success_criteria=objective.success_criteria,
                ),
                PracticeTask(
                    id="practice_2",
                    prompt="Try the same idea again with one changed detail, then explain what stayed the same and what changed.",
                    purpose="variation",
                    success_criteria=objective.success_criteria,
                ),
            ],
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
            practice_tasks=[
                PracticeTask(
                    id="practice_1",
                    prompt="Find one centre, one edge, and one corner on the cube.",
                    purpose="direct_application",
                    success_criteria="Correctly identifies the three piece types.",
                ),
                PracticeTask(
                    id="practice_2",
                    prompt="Turn the cube to a different side and find another centre, edge, and corner.",
                    purpose="variation",
                    success_criteria="Can repeat the identification from a new cube orientation.",
                ),
            ],
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

    def _normalise_practice_tasks(self, lesson: LessonArtifact, objective: Objective) -> list[PracticeTask]:
        original_count = len(lesson.practice_tasks)
        valid_tasks = [
            practice_task
            for practice_task in lesson.practice_tasks
            if practice_task.prompt.strip() and practice_task.success_criteria.strip()
        ]
        normalised_tasks: list[PracticeTask] = []

        for index, practice_task in enumerate(valid_tasks[:2], start=1):
            normalised_tasks.append(
                PracticeTask(
                    id=practice_task.id.strip() or f"practice_{index}",
                    prompt=practice_task.prompt.strip(),
                    purpose=practice_task.purpose.strip() or ("direct_application" if index == 1 else "variation"),
                    success_criteria=practice_task.success_criteria.strip(),
                )
            )

        while len(normalised_tasks) < 2:
            normalised_tasks.append(self._build_default_practice_task(lesson, objective, len(normalised_tasks) + 1))

        if len(valid_tasks) != original_count or len(normalised_tasks) != original_count:
            logger.info(
                "Repaired practice tasks for objective %s: original_count=%s valid_count=%s final_count=%s",
                lesson.objective_id,
                original_count,
                len(valid_tasks),
                len(normalised_tasks),
            )

        return normalised_tasks

    def _build_default_practice_task(self, lesson: LessonArtifact, objective: Objective, index: int) -> PracticeTask:
        if index == 1:
            return PracticeTask(
                id="practice_1",
                prompt=f"Apply the key idea from {lesson.title} to one simple example.",
                purpose="direct_application",
                success_criteria=lesson.practical_task.success_criteria or objective.success_criteria,
            )

        return PracticeTask(
            id="practice_2",
            prompt="Try the same idea again with one changed detail, then note what stayed the same.",
            purpose="variation",
            success_criteria=objective.success_criteria,
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

    def _lesson_validation_errors(self, lesson: LessonArtifact) -> list[str]:
        errors: list[str] = []

        if not lesson.lesson_id.strip() or not lesson.objective_id.strip() or not lesson.title.strip():
            errors.append("missing_identity_fields")

        if not lesson.lesson_html.strip():
            errors.append("missing_lesson_html")

        if len(lesson.key_points) < 3:
            errors.append("key_points_count_lt_3")

        if not lesson.practical_task or not lesson.practical_task.instruction.strip() or not lesson.practical_task.success_criteria.strip():
            errors.append("missing_practical_task")

        if len(lesson.practice_tasks) != 2:
            errors.append("practice_tasks_count_not_2")

        for index, practice_task in enumerate(lesson.practice_tasks, start=1):
            if (
                not practice_task.id.strip()
                or not practice_task.prompt.strip()
                or not practice_task.purpose.strip()
                or not practice_task.success_criteria.strip()
            ):
                errors.append(f"invalid_practice_task_{index}")

        if not lesson.assessment.question.strip() or not lesson.assessment.rubric:
            errors.append("missing_assessment_question_or_rubric")

        if lesson.assessment.type == "short_written_answer" and not lesson.assessment.expected_answer:
            errors.append("missing_short_written_expected_answer")

        return errors


def escape_text(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )
