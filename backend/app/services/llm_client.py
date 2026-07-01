import json
import os
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

        try:
            parsed_json = json.loads(content)
        except json.JSONDecodeError as exc:
            raise LLMClientError("DeepSeek returned invalid JSON content") from exc

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
