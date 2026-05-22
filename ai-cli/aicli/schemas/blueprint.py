"""Blueprint schema.

The blueprint is the single source of truth for generated software.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, field_validator

from aicli.schemas.tasks import TaskDefinition


def _strip_string(value: object) -> object:
    if isinstance(value, str):
        return value.strip()
    return value


def _normalize_text_list(value: object) -> object:
    if value is None:
        return []
    if isinstance(value, str):
        stripped = value.strip()
        return [stripped] if stripped else []
    if isinstance(value, list):
        normalized: list[object] = []
        for item in value:
            if isinstance(item, str):
                stripped = item.strip()
                if stripped:
                    normalized.append(stripped)
                continue
            normalized.append(item)
        return normalized
    return value


def _coerce_string_items(value: object, field_name: str) -> object:
    if not isinstance(value, list):
        return value

    normalized: list[object] = []
    for item in value:
        if isinstance(item, str):
            stripped = item.strip()
            if stripped:
                normalized.append({field_name: stripped})
            continue
        normalized.append(item)
    return normalized


Text = Annotated[str, BeforeValidator(_strip_string)]
RequiredText = Annotated[str, BeforeValidator(_strip_string), Field(min_length=1)]


class BlueprintMetadata(BaseModel):
    """High-level project metadata for future agent orchestration."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = "3.0"
    project_type: Text = ""
    domain: Text = ""
    target_users: list[str] = Field(default_factory=list)

    @field_validator("target_users", mode="before")
    @classmethod
    def normalize_target_users(cls, value: object) -> object:
        """Normalize compact provider output into a clean text list."""

        return _normalize_text_list(value)


class GoalDefinition(BaseModel):
    """Project goal represented in the blueprint."""

    model_config = ConfigDict(extra="forbid")

    title: RequiredText
    description: Text = ""


class PageDefinition(BaseModel):
    """Frontend page entry in the project blueprint."""

    model_config = ConfigDict(extra="forbid")

    name: RequiredText
    path: RequiredText
    description: Text = ""
    user_flows: list[str] = Field(default_factory=list)

    @field_validator("user_flows", mode="before")
    @classmethod
    def normalize_user_flows(cls, value: object) -> object:
        """Normalize compact provider output into a clean text list."""

        return _normalize_text_list(value)


class FeatureDefinition(BaseModel):
    """User-facing capability in the project blueprint."""

    model_config = ConfigDict(extra="forbid")

    name: RequiredText
    description: Text = ""
    requirements: list[str] = Field(default_factory=list)
    user_flows: list[str] = Field(default_factory=list)

    @field_validator("requirements", "user_flows", mode="before")
    @classmethod
    def normalize_text_lists(cls, value: object) -> object:
        """Normalize compact provider output into clean text lists."""

        return _normalize_text_list(value)


class EntityDefinition(BaseModel):
    """Core business entity in the project blueprint."""

    model_config = ConfigDict(extra="forbid")

    name: RequiredText
    description: Text = ""
    attributes: list[str] = Field(default_factory=list)
    relationships: list[str] = Field(default_factory=list)

    @field_validator("attributes", "relationships", mode="before")
    @classmethod
    def normalize_text_lists(cls, value: object) -> object:
        """Normalize compact provider output into clean text lists."""

        return _normalize_text_list(value)


class ModuleDefinition(BaseModel):
    """Product or domain module in the project blueprint."""

    model_config = ConfigDict(extra="forbid")

    name: RequiredText
    description: Text = ""
    responsibilities: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)

    @field_validator("responsibilities", "dependencies", mode="before")
    @classmethod
    def normalize_text_lists(cls, value: object) -> object:
        """Normalize compact provider output into clean text lists."""

        return _normalize_text_list(value)


class ArchitectureNote(BaseModel):
    """Architecture-level note without implementation detail."""

    model_config = ConfigDict(extra="forbid")

    title: Text = ""
    content: RequiredText


class RouteDefinition(BaseModel):
    """Application route entry in the project blueprint."""

    model_config = ConfigDict(extra="forbid")

    path: RequiredText
    target: RequiredText
    description: Text = ""


class DatabaseObject(BaseModel):
    """Database table or object entry in the project blueprint."""

    model_config = ConfigDict(extra="forbid")

    name: RequiredText
    kind: Literal["table", "view", "index", "extension"] = "table"
    columns: dict[str, str] = Field(default_factory=dict)
    relationships: list[str] = Field(default_factory=list)


class ApiDefinition(BaseModel):
    """API contract entry in the project blueprint."""

    model_config = ConfigDict(extra="forbid")

    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
    path: RequiredText
    description: Text = ""
    request_schema: dict[str, Any] = Field(default_factory=dict)
    response_schema: dict[str, Any] = Field(default_factory=dict)


class GeneratedFile(BaseModel):
    """Generated artifact tracked by the blueprint."""

    model_config = ConfigDict(extra="forbid")

    path: RequiredText
    owner: RequiredText
    purpose: Text = ""
    checksum: str | None = None


class ProjectBlueprint(BaseModel):
    """Single source of truth for project generation."""

    model_config = ConfigDict(extra="forbid")

    project_name: Text = ""
    description: Text = ""
    metadata: BlueprintMetadata = Field(default_factory=BlueprintMetadata)
    goals: list[GoalDefinition] = Field(default_factory=list)
    features: list[FeatureDefinition] = Field(default_factory=list)
    entities: list[EntityDefinition] = Field(default_factory=list)
    modules: list[ModuleDefinition] = Field(default_factory=list)
    architecture_notes: list[ArchitectureNote] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    future_enhancements: list[str] = Field(default_factory=list)
    stack: dict[str, str] = Field(default_factory=dict)
    pages: list[PageDefinition] = Field(default_factory=list)
    routes: list[RouteDefinition] = Field(default_factory=list)
    database: list[DatabaseObject] = Field(default_factory=list)
    apis: list[ApiDefinition] = Field(default_factory=list)
    tasks: list[TaskDefinition] = Field(default_factory=list)
    generated_files: list[GeneratedFile] = Field(default_factory=list)

    @field_validator("goals", mode="before")
    @classmethod
    def normalize_goals(cls, value: object) -> object:
        """Accept compact goal strings while storing typed goal objects."""

        return _coerce_string_items(value, "title")

    @field_validator("features", "entities", "modules", mode="before")
    @classmethod
    def normalize_named_items(cls, value: object) -> object:
        """Accept compact strings while storing typed named objects."""

        return _coerce_string_items(value, "name")

    @field_validator("architecture_notes", mode="before")
    @classmethod
    def normalize_architecture_notes(cls, value: object) -> object:
        """Accept compact note strings while storing typed note objects."""

        return _coerce_string_items(value, "content")

    @field_validator("assumptions", "constraints", "future_enhancements", mode="before")
    @classmethod
    def normalize_text_lists(cls, value: object) -> object:
        """Normalize compact provider output into clean text lists."""

        return _normalize_text_list(value)
