"""Integration Agent models."""

from __future__ import annotations

from pydantic import BaseModel

from omnix_cli.schemas.integration import (
    ConflictReport,
    DependencyGraph,
    IntegratedPackage,
    IntegrationReport,
)


class IntegrationAgentResult(BaseModel):
    """Result of an Integration Agent execution."""

    provider: str
    model: str
    package: IntegratedPackage
    dependency_graph: DependencyGraph
    integration_report: IntegrationReport
    conflict_report: ConflictReport
