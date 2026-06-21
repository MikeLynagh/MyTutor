from pydantic import BaseModel
from typing import Literal

class MissionPlanRequest(BaseModel):
    goal: str
    source_mode: Literal["web", "user_material", "both"]
    user_material: str | None = None

class CuratedSource(BaseModel):
    title: str
    url: str
    reason: str

class MissionPlanResponse(BaseModel):
    mission_id: str
    sources: list[CuratedSource]
    summary: str
