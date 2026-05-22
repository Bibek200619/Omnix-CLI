"""Architect Agent internal models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from omnix_cli.schemas.blueprint import ProjectBlueprint


class ArchitectContext(BaseModel):
    """Structured context supplied to the Architect Agent provider."""

    model_config = ConfigDict(extra="forbid")

    goals: list[str] = Field(default_factory=list)
    decisions: list[str] = Field(default_factory=list)
    recent_conversations: list[str] = Field(default_factory=list)
    existing_blueprint: ProjectBlueprint


class ArchitectAgentResult(BaseModel):
    """Structured result of one Architect Agent run."""

    model_config = ConfigDict(extra="forbid")

    provider: str
    model: str
    blueprint: ProjectBlueprint
    feature_count: int
    entity_count: int
    module_count: int
    architecture_note_count: int
