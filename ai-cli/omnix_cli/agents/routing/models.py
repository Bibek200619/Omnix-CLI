"""Routing Agent models."""

from __future__ import annotations

from pydantic import BaseModel

from omnix_cli.schemas.artifacts import Artifact


class RoutingAgentResult(BaseModel):
    """Result of a Routing Agent execution."""

    provider: str
    model: str
    artifact: Artifact
    task_id: str
