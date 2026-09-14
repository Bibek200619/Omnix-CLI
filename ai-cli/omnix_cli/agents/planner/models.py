"""Planner Agent internal models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from omnix_cli.schemas.blueprint import ProjectBlueprint
from omnix_cli.schemas.tasks import TaskPlan


class PlannerContext(BaseModel):
    """Structured context supplied to the Planner Agent provider."""

    model_config = ConfigDict(extra="forbid")

    goals: list[str] = Field(default_factory=list)
    decisions: list[str] = Field(default_factory=list)
    recent_conversations: list[str] = Field(default_factory=list)
    blueprint: ProjectBlueprint
    existing_task_plan: TaskPlan


class PlannerAgentResult(BaseModel):
    """Structured result of one Planner Agent run."""

    model_config = ConfigDict(extra="forbid")

    provider: str
    model: str
    task_plan: TaskPlan
    task_count: int
    new_task_count: int
    updated_task_count: int
    tasks_by_agent: dict[str, int]
