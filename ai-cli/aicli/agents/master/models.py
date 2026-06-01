"""Master Agent internal models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class DetectedMemoryUpdates(BaseModel):
    """Rule-based memory updates detected from a user message."""

    model_config = ConfigDict(extra="forbid")

    goal: str | None = None
    decisions: list[str] = Field(default_factory=list)


class MasterAgentTurn(BaseModel):
    """Persistable summary of one Master Agent turn."""

    model_config = ConfigDict(extra="forbid")

    user_message: str
    assistant_response: str
    detected_goal: str | None = None
    detected_decisions: list[str] = Field(default_factory=list)
    provider: str | None = None
    model: str | None = None
