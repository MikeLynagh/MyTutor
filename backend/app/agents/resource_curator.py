from app.services.web_search import WebSearchService


class ResourceCuratorAgent: 
    def __init__(self, search_service: WebSearchService | None = None):
        self.search_service = search_service or WebSearchService()


    def curate(self, goal: str, source_mode: str, user_material: str | None = None):
        sources = []

        if source_mode in {"web", "both"}:
            sources.extend(self.search_service.search(query=goal))

        if source_mode in {"user_material", "both"} and user_material:
            sources.append(
                {
                    "title": "User-provided material",
                    "url": "user-material://provided",
                    "reason": "Included because the learner provided their own notes or links",
                }
            )

        return {
            "sources": sources,
            "summary": "The available resources suggest starting with the beginner method, learning cube notation, then practicing a layer-by-layer solve.",
        }
