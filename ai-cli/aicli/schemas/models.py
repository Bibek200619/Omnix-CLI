"""Role-to-model configuration schema."""

from __future__ import annotations

from typing import cast

from pydantic import BaseModel, ConfigDict, field_validator

from aicli.schemas.tasks import AgentRole


class ModelsConfig(BaseModel):
    """Fixed agent roles with replaceable model names."""

    model_config = ConfigDict(extra="forbid")

    master: str | None = None
    planner: str | None = None
    architect: str | None = None
    frontend: str | None = None
    backend: str | None = None
    database: str | None = None
    routing: str | None = None
    integration: str | None = None
    qa: str | None = None

    @field_validator("*", mode="before")
    @classmethod
    def normalize_model_name(cls, value: object) -> object:
        """Treat blank model names as unset."""

        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value

    def model_for(self, role: AgentRole) -> str | None:
        """Return the configured model name for a role."""

        return cast(str | None, getattr(self, role.value))

    def with_model(self, role: AgentRole, model_name: str | None) -> ModelsConfig:
        """Return a copy with one role updated."""

        return self.model_copy(update={role.value: model_name})
