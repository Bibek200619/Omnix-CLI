"""Artifact schemas for generated worker outputs."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ArtifactType(StrEnum):
    """Types of artifacts produced by worker agents."""

    FRONTEND_COMPONENT = "frontend_component"
    FRONTEND_PAGE = "frontend_page"
    UI_CONCEPT = "ui_concept"
    FRONTEND_STRUCTURE = "frontend_structure"
    # Backend types
    BACKEND_SERVICE = "backend_service"
    API_DESIGN = "api_design"
    DOMAIN_MODEL = "domain_model"
    BUSINESS_LOGIC = "business_logic"
    SERVICE_CONTRACT = "service_contract"
    # Database types
    SCHEMA_DESIGN = "schema_design"
    RELATIONSHIP_MODEL = "relationship_model"
    MIGRATION_PLAN = "migration_plan"
    DATA_MODEL = "data_model"
    INDEXING_STRATEGY = "indexing_strategy"
    # Routing types
    ROUTE_MAP = "route_map"
    NAVIGATION_STRUCTURE = "navigation_structure"
    API_ROUTE_DEFINITION = "api_route_definition"
    PERMISSION_FLOW = "permission_flow"
    WORKFLOW_MAP = "workflow_map"
    # Future types
    DATABASE_SCHEMA = "database_schema"


class Artifact(BaseModel):
    """A generated output produced by a worker agent."""

    model_config = ConfigDict(extra="forbid")

    id: str
    task_id: str
    agent: str
    title: str
    description: str = ""
    artifact_type: ArtifactType
    generated_at: datetime = Field(default_factory=datetime.now)
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    version: int = 1


class ArtifactList(BaseModel):
    """A collection of artifacts, used for persistence if stored in one file."""

    artifacts: list[Artifact] = Field(default_factory=list)
