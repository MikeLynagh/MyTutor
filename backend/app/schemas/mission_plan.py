from pydantic import BaseModel

from app.schemas.mission import SourceMode
from app.schemas.resources import CuratedResource, RejectedResource


class MissionPlanRequest(BaseModel):
    goal: str
    source_mode: SourceMode
    user_material: str | None = None


class MissionPlanResponse(BaseModel):
    mission_id: str
    selected_sources: list[CuratedResource]
    rejected_sources: list[RejectedResource]
    source_summary: str
    recommended_learning_approach: str
