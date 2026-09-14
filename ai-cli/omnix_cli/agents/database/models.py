"""Database Agent models."""

from __future__ import annotations

from pydantic import BaseModel

from omnix_cli.schemas.artifacts import Artifact


class DatabaseAgentResult(BaseModel):
    """Result of a Database Agent execution."""

    provider: str
    model: str
    artifact: Artifact
    task_id: str
