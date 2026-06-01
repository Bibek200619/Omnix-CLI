"""Persistent project memory schema."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from omnix_cli.schemas.audit import AuditFinding
from omnix_cli.schemas.tasks import AgentRole


def utc_now() -> datetime:
    """Return the current UTC timestamp."""

    return datetime.now(UTC)


class ArchitecturalDecision(BaseModel):
    """Persisted architectural decision."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1)
    rationale: str = ""
    created_at: datetime = Field(default_factory=utc_now)


class GoalStatus(StrEnum):
    """Long-term project goal status."""

    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ConversationRole(StrEnum):
    """Roles persisted in project conversation history."""

    USER = "user"
    ASSISTANT = "assistant"


class ProjectGoal(BaseModel):
    """Long-term objective tracked by the Master Agent."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    created_at: datetime = Field(default_factory=utc_now)
    status: GoalStatus = GoalStatus.ACTIVE


class ConversationEntry(BaseModel):
    """Persisted conversation message."""

    model_config = ConfigDict(extra="forbid")

    role: ConversationRole
    content: str = Field(min_length=1)
    timestamp: datetime = Field(default_factory=utc_now)


class ProjectDecision(BaseModel):
    """Project decision tracked by the Master Agent."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    rationale: str = ""
    created_at: datetime = Field(default_factory=utc_now)


class CompletedTask(BaseModel):
    """Task completion record."""

    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(min_length=1)
    summary: str = ""
    completed_at: datetime = Field(default_factory=utc_now)


class KnownIssue(BaseModel):
    """Known project issue tracked across CLI runs."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1)
    details: str = ""
    blocking: bool = False
    created_at: datetime = Field(default_factory=utc_now)


class GeneratedArtifact(BaseModel):
    """Generated file or artifact memory entry."""

    model_config = ConfigDict(extra="forbid")

    path: str = Field(min_length=1)
    agent: AgentRole
    description: str = ""
    created_at: datetime = Field(default_factory=utc_now)


class AgentOutput(BaseModel):
    """Recorded agent output."""

    model_config = ConfigDict(extra="forbid")

    role: AgentRole
    summary: str = Field(min_length=1)
    content: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class RepairAttempt(BaseModel):
    """Repair-loop memory entry."""

    model_config = ConfigDict(extra="forbid")

    findings: list[AuditFinding] = Field(default_factory=list)
    affected_agents: list[AgentRole] = Field(default_factory=list)
    summary: str = ""
    created_at: datetime = Field(default_factory=utc_now)


class ProjectMemory(BaseModel):
    """Persistent memory that survives CLI restarts."""

    model_config = ConfigDict(extra="forbid")

    project_name: str = ""
    goals: list[ProjectGoal] = Field(default_factory=list)
    conversations: list[ConversationEntry] = Field(default_factory=list)
    decisions: list[ProjectDecision] = Field(default_factory=list)
    architectural_decisions: list[ArchitecturalDecision] = Field(default_factory=list)
    completed_tasks: list[CompletedTask] = Field(default_factory=list)
    known_issues: list[KnownIssue] = Field(default_factory=list)
    generated_artifacts: list[GeneratedArtifact] = Field(default_factory=list)
    agent_outputs: list[AgentOutput] = Field(default_factory=list)
    repair_history: list[RepairAttempt] = Field(default_factory=list)
