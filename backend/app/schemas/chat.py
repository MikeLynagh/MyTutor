from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class MissionChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    current_objective_id: str | None = None
    history: list[ChatMessage] = Field(default_factory=list, max_length=12)


class MissionChatResponse(BaseModel):
    message: ChatMessage


class MissionChatLLMResponse(BaseModel):
    content: str = Field(min_length=1, max_length=1200)
