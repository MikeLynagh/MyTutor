import json
import os
import re
from typing import Protocol, TypeVar

import httpx
from pydantic import BaseModel

StructuredOutputT = TypeVar("StructuredOutputT", bound=BaseModel)


class LLMClientError(Exception):
    pass


class LLMProvider(Protocol):
    def generate_structured(
        self,
        *,
        schema: type[StructuredOutputT],
        system_prompt: str,
        user_prompt: str,
    ) -> StructuredOutputT:
        ...


class MockLLMProvider:
    def generate_structured(
        self,
        *,
        schema: type[StructuredOutputT],
        system_prompt: str,
        user_prompt: str,
    ) -> StructuredOutputT:
        prompt_data = json.loads(user_prompt)
        schema_name = schema.__name__

        if schema_name == "LearningPlan":
            goal = prompt_data.get("mission_goal", "this topic")
            normalized_goal = str(goal).lower()
            if any(keyword in normalized_goal for keyword in ["build", "code", "program", "api", "backend", "frontend", "python"]):
                mission_type = "technical_skill"
            elif any(keyword in normalized_goal for keyword in ["learn", "play", "cook", "draw", "write", "speak"]):
                mission_type = "procedural_skill"
            else:
                mission_type = "conceptual_topic"

            return schema.model_validate(
                {
                    "mission_type": mission_type,
                    "objectives": [
                        {
                            "id": "obj_1",
                            "title": f"Understand the foundations of {goal}",
                            "description": f"Learn the core terms, concepts, and first practical steps for {goal}.",
                            "difficulty": 0.2,
                            "assessment_type": "short_written_answer",
                            "prerequisites": [],
                            "success_criteria": f"Learner can explain the key foundations of {goal} clearly.",
                        },
                        {
                            "id": "obj_2",
                            "title": f"Practice a guided workflow for {goal}",
                            "description": f"Work through a guided example or structured practice sequence for {goal}.",
                            "difficulty": 0.55,
                            "assessment_type": "practical_check",
                            "prerequisites": ["obj_1"],
                            "success_criteria": f"Learner can complete a guided practice flow for {goal} and explain each step.",
                        },
                        {
                            "id": "obj_3",
                            "title": f"Apply {goal} independently",
                            "description": f"Complete a small independent task that demonstrates working ability in {goal}.",
                            "difficulty": 0.85,
                            "assessment_type": "practical_check",
                            "prerequisites": ["obj_2"],
                            "success_criteria": f"Learner can complete a small independent task in {goal} with minimal support.",
                        },
                    ],
                    "diagnostic_questions": [
                        f"What experience do you already have with {goal}?",
                        f"What part of {goal} feels most unfamiliar right now?",
                        f"What would a successful first practical win in {goal} look like for you?",
                    ],
                }
            )

        if schema_name == "LessonArtifact":
            objective = prompt_data.get("objective", {})
            title = objective.get("title", "Lesson")
            description = objective.get("description", "")
            success_criteria = objective.get("success_criteria", "")
            assessment_type = objective.get("assessment_type", "short_written_answer")
            normalized_goal = str(prompt_data.get("mission_goal", "")).lower()

            if "rubik" in normalized_goal or "cube" in normalized_goal:
                payload = {
                    "lesson_id": "draft",
                    "objective_id": objective.get("id", "obj_1"),
                    "title": "Cube pieces and notation",
                    "lesson_html": (
                        "<article>"
                        "<h2>Cube pieces and notation</h2>"
                        "<section><h3>Piece types</h3><p>Centres have one colour, edges have two colours, and corners have three colours.</p></section>"
                        "<section><h3>Notation</h3><p>R, U, F, L, D, and B are the moves you need first.</p></section>"
                        "<section><h3>Practice</h3><p>Identify four edge pieces and four corner pieces on your cube.</p></section>"
                        "</article>"
                    ),
                    "key_points": [
                        "Centres have one colour.",
                        "Edges have two colours.",
                        "Corners have three colours.",
                    ],
                    "practical_task": {
                        "instruction": "Pick up your cube and identify four edge pieces and four corner pieces.",
                        "success_criteria": "The learner can correctly distinguish centre, edge, and corner pieces.",
                    },
                    "practice_tasks": [
                        {
                            "id": "practice_1",
                            "prompt": "Find one centre, one edge, and one corner on the cube.",
                            "purpose": "direct_application",
                            "success_criteria": "Correctly identifies the three piece types.",
                        },
                        {
                            "id": "practice_2",
                            "prompt": "Turn the cube to a different side and find another centre, edge, and corner.",
                            "purpose": "variation",
                            "success_criteria": "Can repeat the identification from a new cube orientation.",
                        },
                    ],
                    "assessment": {
                        "type": "short_written_answer",
                        "question": "Explain the difference between centre, edge, and corner pieces in your own words.",
                        "expected_answer": "Centres have one colour, edges have two colours, and corners have three colours.",
                        "rubric": [
                            "Mentions centres have one colour",
                            "Mentions edges have two colours",
                            "Mentions corners have three colours",
                        ],
                        "options": [],
                    },
                }
            else:
                payload = {
                    "lesson_id": "draft",
                    "objective_id": objective.get("id", "obj_1"),
                    "title": title,
                    "lesson_html": (
                        "<article>"
                        f"<h2>{title}</h2>"
                        f"<p>{description}</p>"
                        "<section><h3>Key idea</h3><p>Focus on the core concept first, then practice a guided example.</p></section>"
                        "<section><h3>Practice</h3><p>Complete one small step-by-step example tied to the objective.</p></section>"
                        "</article>"
                    ),
                    "key_points": [
                        f"Understand the key idea behind {title}.",
                        "Follow the guided example carefully.",
                        f"Use the success criteria to check whether you can do {title} independently.",
                    ],
                    "practical_task": {
                        "instruction": f"Complete one guided example related to {title}.",
                        "success_criteria": success_criteria or f"You can demonstrate the core idea behind {title}.",
                    },
                    "practice_tasks": [
                        {
                            "id": "practice_1",
                            "prompt": f"Apply the key idea from {title} to one simple example.",
                            "purpose": "direct_application",
                            "success_criteria": success_criteria or f"You can demonstrate the core idea behind {title}.",
                        },
                        {
                            "id": "practice_2",
                            "prompt": "Try the same idea again with one changed detail, then note what stayed the same.",
                            "purpose": "variation",
                            "success_criteria": success_criteria or f"You can transfer the idea to a small variation of the task.",
                        },
                    ],
                    "assessment": {
                        "type": assessment_type,
                        "question": f"Explain or demonstrate the core idea behind {title}.",
                        "expected_answer": success_criteria or f"You can demonstrate the core idea behind {title}.",
                        "rubric": [
                            "Addresses the core idea",
                            "Matches the objective success criteria",
                            "Shows the learner can apply the idea",
                        ],
                        "options": [],
                    },
                }

            return schema.model_validate(payload)

        if schema_name == "EvaluationResult":
            learner_answer = str(prompt_data.get("learner_answer", "")).lower()
            rubric = prompt_data.get("rubric", [])
            expected_answer = str(prompt_data.get("expected_answer", "")).lower()
            normalized_context = f"{expected_answer} {' '.join(rubric)}".lower()

            required_terms = []
            if "centre" in normalized_context or "center" in normalized_context:
                required_terms.append(("centre", ["centre", "center", "one colour", "one color"]))
            if "edge" in normalized_context:
                required_terms.append(("edge", ["edge", "two colours", "two colors"]))
            if "corner" in normalized_context:
                required_terms.append(("corner", ["corner", "three colours", "three colors"]))

            if required_terms:
                matched_terms = [
                    label
                    for label, aliases in required_terms
                    if any(alias in learner_answer for alias in aliases)
                ]
                score = len(matched_terms) / len(required_terms)
                missing_points = [
                    f"Mentions {label} pieces accurately"
                    for label, _aliases in required_terms
                    if label not in matched_terms
                ]
            else:
                answer_tokens = {token for token in re.findall(r"[a-zA-Z]{4,}", learner_answer)}
                expected_tokens = {token for token in re.findall(r"[a-zA-Z]{4,}", expected_answer)}
                overlap = answer_tokens & expected_tokens
                score = min(1.0, len(overlap) / max(1, len(expected_tokens) * 0.5))
                missing_points = list(rubric)[:3] if score < 0.7 else []

            is_correct = score >= 0.75
            return schema.model_validate(
                {
                    "is_correct": is_correct,
                    "score": round(score, 2),
                    "feedback": (
                        "Good answer. It matches the assessment criteria."
                        if is_correct
                        else "Your answer is on the right track, but it misses part of the assessment criteria."
                    ),
                    "misconception": None if is_correct else "Some required assessment points are missing or unclear.",
                    "missing_points": missing_points,
                    "next_hint": None if is_correct else (missing_points[0] if missing_points else "Review the key points and try again."),
                }
            )

        if schema_name == "MissionChatLLMResponse":
            message = str(prompt_data.get("message", "")).strip()
            mission_goal = str(prompt_data.get("mission", {}).get("goal", "this mission"))
            lesson = prompt_data.get("current_lesson") or {}
            lesson_title = lesson.get("title") or "the current lesson"
            return schema.model_validate(
                {
                    "content": (
                        f"For your mission to {mission_goal}, focus on {lesson_title}. "
                        f"Your question was: {message}. Use the current lesson steps and success criteria to check your understanding."
                    )
                }
            )

        goal = prompt_data.get("mission_goal", "this topic")
        search_results = prompt_data.get("search_results", [])

        selected_sources = []
        rejected_sources = []

        for result in search_results:
            title_and_snippet = f"{result['title']} {result['snippet']}".lower()
            if "advanced" in title_and_snippet or "cfop" in title_and_snippet or "speedcub" in title_and_snippet:
                rejected_sources.append(
                    {
                        "title": result["title"],
                        "url": result["url"],
                        "reason": "Too advanced for the learner's current starting point.",
                    }
                )
                continue

            selected_sources.append(
                {
                    "title": result["title"],
                    "url": result["url"],
                    "type": "guide" if "guide" in title_and_snippet or "beginner" in title_and_snippet else "article",
                    "reason": f"Useful beginner-oriented source for {goal}.",
                }
            )

        normalized_goal = str(goal).lower()
        payload = {
            "selected_sources": selected_sources[:2],
            "rejected_sources": rejected_sources,
            "source_summary": (
                "Beginner Rubik's cube resources should introduce notation first and then teach a layer-by-layer solving method."
                if "rubik" in normalized_goal or "cube" in normalized_goal
                else f"Selected resources for {goal} appear suitable for an introductory learning path."
            ),
            "recommended_learning_approach": (
                "beginner_layer_by_layer"
                if "rubik" in normalized_goal or "cube" in normalized_goal
                else "guided_foundations"
            ),
        }
        return schema.model_validate(payload)


class DeepSeekProvider:
    def __init__(
        self,
        *,
        api_key: str,
        model: str | None = None,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model or os.getenv("DEEPSEEK_MODEL", "deepseek-v4-pro")
        self.base_url = (base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")).rstrip("/")
        self.timeout_seconds = timeout_seconds or float(os.getenv("LLM_TIMEOUT_SECONDS", "60"))

    def generate_structured(
        self,
        *,
        schema: type[StructuredOutputT],
        system_prompt: str,
        user_prompt: str,
    ) -> StructuredOutputT:
        schema_json = json.dumps(schema.model_json_schema(), indent=2)
        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                f"{system_prompt}\n\n"
                                "Return valid json only. Follow this JSON schema exactly:\n"
                                f"{schema_json}"
                            ),
                        },
                        {"role": "user", "content": user_prompt},
                    ],
                    "response_format": {"type": "json_object"},
                    "stream": False,
                },
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise LLMClientError(
                f"DeepSeek request failed with status {exc.response.status_code}: {exc.response.text[:500]}"
            ) from exc
        except httpx.TimeoutException as exc:
            raise LLMClientError(f"DeepSeek request timed out after {self.timeout_seconds} seconds") from exc
        except httpx.HTTPError as exc:
            raise LLMClientError(f"DeepSeek request failed: {exc}") from exc

        response_json = response.json()
        content = response_json["choices"][0]["message"]["content"]
        if not content:
            raise LLMClientError("DeepSeek returned empty content for structured output")

        parsed_json = parse_json_content(content)

        try:
            return schema.model_validate(parsed_json)
        except Exception as exc:
            raise LLMClientError("DeepSeek returned JSON that did not match the target schema") from exc


class LLMClient:
    def __init__(self, provider: LLMProvider | None = None, provider_name: str | None = None):
        self.provider = provider or self._build_provider(provider_name)

    def generate_structured(
        self,
        *,
        schema: type[StructuredOutputT],
        system_prompt: str,
        user_prompt: str,
    ) -> StructuredOutputT:
        return self.provider.generate_structured(
            schema=schema,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

    def _build_provider(self, provider_name: str | None) -> LLMProvider:
        selected_provider = (provider_name or os.getenv("LLM_PROVIDER", "mock")).lower()

        if selected_provider == "mock":
            return MockLLMProvider()

        if selected_provider == "deepseek":
            api_key = os.getenv("DEEPSEEK_API_KEY")
            if not api_key:
                raise LLMClientError("DEEPSEEK_API_KEY is required when LLM_PROVIDER=deepseek")
            return DeepSeekProvider(api_key=api_key)

        raise LLMClientError(f"Unsupported LLM provider: {selected_provider}")


def parse_json_content(content: str):
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    fenced_match = re.search(r"```(?:json)?\s*(.*?)\s*```", content, flags=re.DOTALL | re.IGNORECASE)
    if fenced_match:
        try:
            return json.loads(fenced_match.group(1))
        except json.JSONDecodeError:
            pass

    decoder = json.JSONDecoder()
    for index, character in enumerate(content):
        if character not in "{[":
            continue
        try:
            parsed, _ = decoder.raw_decode(content[index:])
            return parsed
        except json.JSONDecodeError:
            continue

    raise LLMClientError("DeepSeek returned invalid JSON content")
