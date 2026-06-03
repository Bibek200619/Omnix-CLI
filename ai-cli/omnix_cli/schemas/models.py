"""Role-to-provider/model configuration schema."""

from __future__ import annotations

from typing import cast

from pydantic import BaseModel, ConfigDict, field_validator

from omnix_cli.schemas.tasks import AgentRole


class ModelAssignment(BaseModel):
    """Provider and model selection for one agent role."""

    model_config = ConfigDict(extra="forbid")

    provider: str | None = None
    model: str | None = None

    @field_validator("provider", "model", mode="before")
    @classmethod
    def normalize_optional_string(cls, value: object) -> object:
        """Treat blank provider/model strings as unset."""

        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value

    @field_validator("provider")
    @classmethod
    def normalize_provider_name(cls, value: str | None) -> str | None:
        """Provider names are case-insensitive in project state."""

        return value.lower() if value else None


class ModelsConfig(BaseModel):
    """Fixed agent roles with replaceable provider/model assignments."""

    model_config = ConfigDict(extra="forbid")

    master: ModelAssignment | None = None
    planner: ModelAssignment | None = None
    architect: ModelAssignment | None = None
    frontend: ModelAssignment | None = None
    backend: ModelAssignment | None = None
    database: ModelAssignment | None = None
    routing: ModelAssignment | None = None
    integration: ModelAssignment | None = None
    qa: ModelAssignment | None = None
    repair: ModelAssignment | None = None

    @field_validator("*", mode="before")
    @classmethod
    def normalize_assignment(cls, value: object) -> object:
        """Accept Phase 0 role strings and Phase 1 assignment objects."""

        if isinstance(value, str):
            stripped = value.strip()
            return {"model": stripped} if stripped else None
        return value

    def assignment_for(self, role: AgentRole) -> ModelAssignment | None:
        """Return the provider/model assignment for a role."""

        return cast(ModelAssignment | None, getattr(self, role.value))

    def model_for(self, role: AgentRole) -> str | None:
        """Return the configured model name for a role."""

        assignment = self.assignment_for(role)
        return assignment.model if assignment else None

    def provider_for(self, role: AgentRole) -> str | None:
        """Return the configured provider name for a role."""

        assignment = self.assignment_for(role)
        return assignment.provider if assignment else None

    def with_model(self, role: AgentRole, model_name: str | None) -> ModelsConfig:
        """Return a copy with one role updated."""

        existing_assignment = self.assignment_for(role)
        provider_name = existing_assignment.provider if existing_assignment else None
        return self.with_assignment(role, provider=provider_name, model=model_name)

    def with_assignment(
        self,
        role: AgentRole,
        *,
        provider: str | None,
        model: str | None,
    ) -> ModelsConfig:
        """Return a copy with one provider/model assignment updated."""

        assignment = ModelAssignment(provider=provider, model=model)
        updated_value: ModelAssignment | None = (
            assignment if assignment.provider or assignment.model else None
        )
        payload = self.model_dump(mode="python")
        payload[role.value] = updated_value
        return type(self).model_validate(payload)

    def legacy_model_dump(self) -> dict[str, str | None]:
        """Return the Phase 0 role-to-model view."""

        return {role.value: self.model_for(role) for role in AgentRole}
