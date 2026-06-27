import os
from typing import Protocol, TypedDict
from urllib.parse import urlparse


class SearchResult(TypedDict):
    title: str
    url: str
    snippet: str


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
