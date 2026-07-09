from typing import Literal

from pydantic import BaseModel, Field


ResourceType = Literal[
    "article",
    "video",
    "documentation",
    "guide",
    "user_material",
    "other",
]


class CuratedResource(BaseModel):
    title: str
    url: str
    type: ResourceType = "other"
    reason: str
    highlights: list[str] = Field(default_factory=list)


class RejectedResource(BaseModel):
    title: str
    url: str
    reason: str


class CuratedResourceBundle(BaseModel):
    selected_sources: list[CuratedResource] = Field(default_factory=list)
    rejected_sources: list[RejectedResource] = Field(default_factory=list)
    source_summary: str
    recommended_learning_approach: str
