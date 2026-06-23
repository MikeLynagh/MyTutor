from typing import TypedDict

class SearchResult(TypedDict):
    title: str
    url: str
    reason: str

class WebSearchService:
    def search(self, query: str) -> list[SearchResult]:
        return [
            {
                "title": "Beginner Rubik's cube guide",
                "url": "https://solvethecube.com/",
                "reason": "Clear beginner-friendly steps",
            },
            {
                "title": "Cube notation basics",
                "url": "https://example.com/cube-notation",
                "reason": "Explains R, U, F, L, D, B notation",
            },
        ]
