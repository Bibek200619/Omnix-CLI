"""Blueprint schema.

The blueprint is the single source of truth for generated software.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from aicli.schemas.tasks import TaskDefinition


class PageDefinition(BaseModel):
    """Frontend page entry in the project blueprint."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    path: str = Field(min_length=1)
    description: str = ""


class RouteDefinition(BaseModel):
    """Application route entry in the project blueprint."""

    model_config = ConfigDict(extra="forbid")

    path: str = Field(min_length=1)
    target: str = Field(min_length=1)
    description: str = ""


class DatabaseObject(BaseModel):
    """Database table or object entry in the project blueprint."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    kind: Literal["table", "view", "index", "extension"] = "table"
    columns: dict[str, str] = Field(default_factory=dict)
    relationships: list[str] = Field(default_factory=list)


class ApiDefinition(BaseModel):
    """API contract entry in the project blueprint."""

    model_config = ConfigDict(extra="forbid")

    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
    path: str = Field(min_length=1)
    description: str = ""
    request_schema: dict[str, Any] = Field(default_factory=dict)
    response_schema: dict[str, Any] = Field(default_factory=dict)


class GeneratedFile(BaseModel):
    """Generated artifact tracked by the blueprint."""

    model_config = ConfigDict(extra="forbid")

    path: str = Field(min_length=1)
    owner: str = Field(min_length=1)
    purpose: str = ""
    checksum: str | None = None


class ProjectBlueprint(BaseModel):
    """Single source of truth for project generation."""

    model_config = ConfigDict(extra="forbid")

    project_name: str = ""
    description: str = ""
    stack: dict[str, str] = Field(default_factory=dict)
    pages: list[PageDefinition] = Field(default_factory=list)
    routes: list[RouteDefinition] = Field(default_factory=list)
    database: list[DatabaseObject] = Field(default_factory=list)
    apis: list[ApiDefinition] = Field(default_factory=list)
    tasks: list[TaskDefinition] = Field(default_factory=list)
    generated_files: list[GeneratedFile] = Field(default_factory=list)
