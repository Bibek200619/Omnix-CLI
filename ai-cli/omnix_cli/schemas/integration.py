"""Schemas for the Integration Agent and Integrated Package."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from omnix_cli.schemas.artifacts import Artifact


class IntegrationStatus(StrEnum):
    """Status of the integration process."""

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    STALE = "stale"


class DependencyType(StrEnum):
    """Types of dependencies between project elements."""

    FRONTEND_TO_BACKEND = "frontend_to_backend"
    BACKEND_TO_DATABASE = "backend_to_database"
    ROUTING_TO_FRONTEND = "routing_to_frontend"
    ROUTING_TO_BACKEND = "routing_to_backend"
    WORKFLOW_DEPENDENCY = "workflow_dependency"
    FEATURE_DEPENDENCY = "feature_dependency"
    DATA_MODEL_DEPENDENCY = "data_model_dependency"


class Dependency(BaseModel):
    """A relationship between two components."""

    source_id: str
    target_id: str
    dependency_type: DependencyType
    description: str = ""


class ConflictSeverity(StrEnum):
    """Severity of a detected conflict."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Conflict(BaseModel):
    """A detected inconsistency between artifacts or blueprint."""

    id: str
    title: str
    description: str
    severity: ConflictSeverity
    involved_artifact_ids: list[str] = Field(default_factory=list)
    involved_blueprint_references: list[str] = Field(default_factory=list)


class CoverageSummary(BaseModel):
    """Analysis of project implementation coverage."""

    total_pages: int = 0
    implemented_pages: int = 0
    total_apis: int = 0
    implemented_apis: int = 0
    total_entities: int = 0
    implemented_entities: int = 0
    gaps: list[str] = Field(default_factory=list)


class IntegratedPackage(BaseModel):
    """The unified representation of the project's current generated state."""

    model_config = ConfigDict(extra="forbid")

    project_name: str
    generated_at: datetime = Field(default_factory=datetime.now)
    version: str = "1.0.0"
    
    # Core Data
    pages: list[dict[str, Any]] = Field(default_factory=list)
    features: list[dict[str, Any]] = Field(default_factory=list)
    entities: list[dict[str, Any]] = Field(default_factory=list)
    apis: list[dict[str, Any]] = Field(default_factory=list)
    routes: list[dict[str, Any]] = Field(default_factory=list)
    workflows: list[dict[str, Any]] = Field(default_factory=list)
    
    # Integration State
    dependencies: list[Dependency] = Field(default_factory=list)
    artifacts: list[Artifact] = Field(default_factory=list)
    conflicts: list[Conflict] = Field(default_factory=list)
    coverage: CoverageSummary = Field(default_factory=CoverageSummary)
    
    status: IntegrationStatus = IntegrationStatus.SUCCESS
    metadata: dict[str, Any] = Field(default_factory=dict)


class DependencyGraph(BaseModel):
    """A machine-readable representation of project dependencies."""

    nodes: list[dict[str, Any]] = Field(default_factory=list)
    edges: list[Dependency] = Field(default_factory=list)


class ConflictReport(BaseModel):
    """A report detailing all detected conflicts."""

    project_name: str
    timestamp: datetime = Field(default_factory=datetime.now)
    total_conflicts: int
    conflicts: list[Conflict]


class IntegrationReport(BaseModel):
    """A high-level summary of the integration process."""

    project_name: str
    timestamp: datetime = Field(default_factory=datetime.now)
    status: IntegrationStatus
    artifacts_processed: int
    artifacts_by_agent: dict[str, int]
    dependencies_found: int
    conflicts_found: int
    coverage_status: str  # e.g., "COMPLETE", "INCOMPLETE"
    summary: str
