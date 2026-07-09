import os
from typing import Protocol, TypedDict
from urllib.parse import urlparse

import httpx


class SearchResult(TypedDict):
    title: str
    url: str
    snippet: str


class WebSearchError(Exception):
    pass


class SearchProvider(Protocol):
    def search(self, query: str) -> list[SearchResult]:
        ...


class MockSearchProvider:
    def search(self, query: str) -> list[SearchResult]:
        normalized_query = query.lower()

        if "rubik" in normalized_query or "cube" in normalized_query:
            return [
                {
                    "title": "Beginner Rubik's cube layer-by-layer guide",
                    "url": "https://example.com/rubiks-beginner",
                    "snippet": "A step-by-step beginner method for solving a 3x3 cube layer by layer.",
                },
                {
                    "title": "Cube notation basics",
                    "url": "https://example.com/cube-notation",
                    "snippet": "Learn what R, U, F, L, D, and B mean before attempting algorithms.",
                }
            ]

        return [
            {
                "title": f"Beginner guide to {query}",
                "url": "https://example.com/beginner-guide",
                "snippet": f"A beginner-friendly introduction to {query} with practical first steps.",
            },
            {
                "title": f"Practice exercises for {query}",
                "url": "https://example.com/practice-exercises",
                "snippet": f"Simple exercises and drills to build confidence while learning {query}.",
            }
        ]


class ExaSearchProvider:
    def __init__(
        self,
        *,
        api_key: str,
        search_type: str | None = None,
        num_results: int | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self.api_key = api_key
        self.search_type = search_type or os.getenv("EXA_SEARCH_TYPE", "auto")
        self.num_results = num_results or int(os.getenv("EXA_NUM_RESULTS", "8"))
        self.timeout_seconds = timeout_seconds or float(os.getenv("EXA_TIMEOUT_SECONDS", "15"))

    def search(self, query: str) -> list[SearchResult]:
        try:
            response = httpx.post(
                "https://api.exa.ai/search",
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": self.api_key,
                },
                json={
                    "query": query,
                    "type": self.search_type,
                    "numResults": self.num_results,
                    "contents": {
                        "highlights": True,
                    },
                },
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise WebSearchError(
                f"Exa search failed with status {exc.response.status_code}: {exc.response.text[:300]}"
            ) from exc
        except httpx.TimeoutException as exc:
            raise WebSearchError(f"Exa search timed out after {self.timeout_seconds} seconds") from exc
        except httpx.HTTPError as exc:
            raise WebSearchError(f"Exa search failed: {exc}") from exc

        payload = response.json()
        return [self._result_to_search_result(result) for result in payload.get("results", [])]

    def _result_to_search_result(self, result: dict) -> SearchResult:
        highlights = result.get("highlights") or []
        snippet = ""
        if highlights:
            snippet = " ".join(str(highlight).strip() for highlight in highlights if highlight).strip()
        if not snippet:
            snippet = str(result.get("summary") or result.get("text") or "").strip()

        return {
            "title": str(result.get("title") or "Untitled result"),
            "url": str(result.get("url") or ""),
            "snippet": snippet,
        }


class WebSearchService:
    def __init__(self, provider: SearchProvider | None = None, provider_name: str | None = None):
        self.provider = provider or self._build_provider(provider_name)

    def search(self, query: str) -> list[SearchResult]:
        raw_results = self.provider.search(query)
        return [result for result in (self._normalize_result(item) for item in raw_results) if result is not None]

    def _build_provider(self, provider_name: str | None) -> SearchProvider:
        selected_provider = (provider_name or os.getenv("WEB_SEARCH_PROVIDER", "mock")).lower()

        if selected_provider == "mock":
            return MockSearchProvider()

        if selected_provider == "exa":
            api_key = os.getenv("EXA_API_KEY")
            if not api_key:
                raise WebSearchError("EXA_API_KEY is required when WEB_SEARCH_PROVIDER=exa")
            return ExaSearchProvider(api_key=api_key)

        raise ValueError(f"Unsupported web search provider: {selected_provider}")

    def _normalize_result(self, result: SearchResult) -> SearchResult | None:
        parsed_url = urlparse(result["url"])
        if parsed_url.scheme not in {"http", "https"}:
            return None

        return {
            "title": result["title"].strip()[:200],
            "url": result["url"].strip(),
            "snippet": result["snippet"].strip()[:500],
        }
