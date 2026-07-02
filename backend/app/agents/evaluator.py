import json
import logging
import re

from app.schemas.evaluation import EvaluationResult
from app.schemas.lesson import Assessment
from app.schemas.plan import Objective
from app.services.llm_client import LLMClient, LLMClientError

logger = logging.getLogger(__name__)


class EvaluatorAgent:
    def __init__(self, llm_client: LLMClient | None = None):
        self.llm_client = llm_client or LLMClient()

    def evaluate_answer(
        self,
        *,
        objective: Objective,
        assessment: Assessment,
        learner_answer: str,
    ) -> EvaluationResult:
        generated = self._evaluate_with_llm(
            objective=objective,
            assessment=assessment,
            learner_answer=learner_answer,
        )
        if generated is not None:
            return generated

        return self._fallback_evaluation(
            objective=objective,
            assessment=assessment,
            learner_answer=learner_answer,
        )

    def _evaluate_with_llm(
        self,
        *,
        objective: Objective,
        assessment: Assessment,
        learner_answer: str,
    ) -> EvaluationResult | None:
        system_prompt = (
            "You are an assessment evaluator for a learning mission. "
            "Evaluate only the supplied learner answer against the objective, expected answer, and rubric. "
            "Do not require wording to match exactly. "
            "Reward correct equivalent explanations. "
            "Be specific, concise, and formative. "
            "Return valid json only and follow the schema exactly."
        )
        user_prompt = json.dumps(
            {
                "objective": {
                    "id": objective.id,
                    "title": objective.title,
                    "success_criteria": objective.success_criteria,
                },
                "assessment_question": assessment.question,
                "expected_answer": assessment.expected_answer,
                "rubric": assessment.rubric,
                "learner_answer": learner_answer,
                "scoring_guidance": {
                    "score_range": "0 to 1",
                    "is_correct_threshold": 0.75,
                    "feedback_style": "specific, non-punitive, tells the learner what to fix",
                    "do_not_decide_mastery": True,
                    "do_not_choose_next_objective": True,
                },
            },
            indent=2,
        )

        try:
            return self.llm_client.generate_structured(
                schema=EvaluationResult,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
        except LLMClientError as exc:
            logger.warning("LLM answer evaluation failed: %s", exc)
            return None

    def _fallback_evaluation(
        self,
        *,
        objective: Objective,
        assessment: Assessment,
        learner_answer: str,
    ) -> EvaluationResult:
        answer = learner_answer.lower()
        expected_context = f"{assessment.expected_answer or ''} {' '.join(assessment.rubric)}".lower()

        rubik_checks = self._rubik_piece_checks(expected_context, answer)
        if rubik_checks is not None:
            score, missing_points = rubik_checks
        else:
            score, missing_points = self._token_overlap_score(
                expected_answer=assessment.expected_answer or objective.success_criteria,
                rubric=assessment.rubric,
                learner_answer=learner_answer,
            )

        is_correct = score >= 0.75
        return EvaluationResult(
            is_correct=is_correct,
            score=round(score, 2),
            feedback=(
                "Good answer. It matches the assessment criteria."
                if is_correct
                else "Your answer is on the right track, but it misses part of the assessment criteria."
            ),
            misconception=None if is_correct else "Some required assessment points are missing or unclear.",
            missing_points=missing_points,
            next_hint=None if is_correct else (missing_points[0] if missing_points else "Review the key points and try again."),
        )

    def _rubik_piece_checks(self, expected_context: str, learner_answer: str) -> tuple[float, list[str]] | None:
        required_terms: list[tuple[str, list[str], str]] = []

        if "centre" in expected_context or "center" in expected_context:
            required_terms.append(
                (
                    "centre",
                    ["centre", "center", "one colour", "one color", "1 colour", "1 color"],
                    "Centres have one colour and sit in the middle of each face.",
                )
            )
        if "edge" in expected_context:
            required_terms.append(
                (
                    "edge",
                    ["edge", "two colours", "two colors", "2 colours", "2 colors"],
                    "Edges have two colours.",
                )
            )
        if "corner" in expected_context:
            required_terms.append(
                (
                    "corner",
                    ["corner", "three colours", "three colors", "3 colours", "3 colors"],
                    "Corners have three colours.",
                )
            )

        if not required_terms:
            return None

        missing_points = [
            missing_point
            for _label, aliases, missing_point in required_terms
            if not any(alias in learner_answer for alias in aliases)
        ]
        score = (len(required_terms) - len(missing_points)) / len(required_terms)
        return score, missing_points

    def _token_overlap_score(
        self,
        *,
        expected_answer: str,
        rubric: list[str],
        learner_answer: str,
    ) -> tuple[float, list[str]]:
        answer_tokens = self._significant_tokens(learner_answer)
        expected_tokens = self._significant_tokens(expected_answer)
        overlap = answer_tokens & expected_tokens

        if not expected_tokens:
            return 0.2, rubric[:3]

        score = min(1.0, len(overlap) / max(1, len(expected_tokens) * 0.5))
        missing_points = [] if score >= 0.7 else rubric[:3]
        return score, missing_points

    def _significant_tokens(self, value: str) -> set[str]:
        stop_words = {
            "about",
            "after",
            "answer",
            "because",
            "before",
            "being",
            "could",
            "their",
            "there",
            "these",
            "those",
            "which",
            "would",
        }
        return {
            token
            for token in re.findall(r"[a-zA-Z]{4,}", value.lower())
            if token not in stop_words
        }
