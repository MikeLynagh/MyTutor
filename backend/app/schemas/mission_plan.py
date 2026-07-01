from pydantic import BaseModel

from app.schemas.mission import MissionType, SourceMode
from app.schemas.plan import Objective
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
    mission_type: MissionType
    objectives: list[Objective]
    diagnostic_questions: list[str]
