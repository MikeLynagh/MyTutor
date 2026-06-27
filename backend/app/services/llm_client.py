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
        timeout_seconds: float = 30.0,
    ) -> None:
        self.api_key = api_key
        self.model = model or os.getenv("DEEPSEEK_MODEL", "deepseek-v4-pro")
        self.base_url = (base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")).rstrip("/")
        self.timeout_seconds = timeout_seconds

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
        except httpx.HTTPError as exc:
            raise LLMClientError("DeepSeek request failed") from exc

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
