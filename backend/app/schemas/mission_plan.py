from pydantic import BaseModel

from app.schemas.mission import SourceMode
from app.schemas.resources import CuratedResource


class MissionPlanRequest(BaseModel):
    goal: str
    source_mode: SourceMode
    user_material: str | None = None


class MissionPlanResponse(BaseModel):
    mission_id: str
    sources: list[CuratedResource]
    summary: str
