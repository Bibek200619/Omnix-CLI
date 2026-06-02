"""Schemas for Phase 9: Parallel Multi-Agent Execution."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class TaskExecutionStatus(StrEnum):
    """Lifecycle state of a single task within an execution run."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ExecutionStrategy(StrEnum):
    """How the coordinator will schedule batches."""

    PARALLEL = "parallel"     # independent tasks run concurrently within a batch
    SEQUENTIAL = "sequential"  # fallback — tasks run one at a time


class TaskExecutionResult(BaseModel):
    """Outcome of executing a single task."""

    model_config = ConfigDict(extra="forbid")

    task_id: str
    task_title: str
    assigned_agent: str
    status: TaskExecutionStatus
    artifact_id: str | None = None
    error: str | None = None
    started_at: datetime = Field(default_factory=datetime.now)
    finished_at: datetime | None = None
    duration_seconds: float = 0.0


class ExecutionBatch(BaseModel):
    """A group of task IDs that can be dispatched simultaneously."""

    model_config = ConfigDict(extra="forbid")

    batch_index: int          # 0-based position in execution order
    task_ids: list[str]       # tasks in this batch (no dependency on each other)


class ExecutionPlan(BaseModel):
    """The full DAG-derived execution schedule for a project's tasks."""

    model_config = ConfigDict(extra="forbid")

    project_name: str
    created_at: datetime = Field(default_factory=datetime.now)
    strategy: ExecutionStrategy = ExecutionStrategy.PARALLEL
    total_tasks: int
    batches: list[ExecutionBatch] = Field(default_factory=list)
    # task_id → list of task_ids it depends on
    dependency_map: dict[str, list[str]] = Field(default_factory=dict)
    # task_id → assigned agent name
    agent_map: dict[str, str] = Field(default_factory=dict)


class ExecutionRunStatus(StrEnum):
    """Overall outcome of one full execution run."""

    SUCCESS = "success"
    PARTIAL = "partial"    # some tasks completed, some failed/skipped
    FAILED = "failed"      # all tasks failed
    EMPTY = "empty"        # no tasks to execute


class ExecutionReport(BaseModel):
    """Summary report for one execution run."""

    model_config = ConfigDict(extra="forbid")

    project_name: str
    run_id: str
    started_at: datetime
    finished_at: datetime = Field(default_factory=datetime.now)
    duration_seconds: float = 0.0
    strategy: ExecutionStrategy
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    skipped_tasks: int
    total_batches: int
    artifacts_generated: int
    workers_used: list[str] = Field(default_factory=list)
    task_results: list[TaskExecutionResult] = Field(default_factory=list)
    status: ExecutionRunStatus

    @property
    def completion_rate(self) -> float:
        if self.total_tasks == 0:
            return 0.0
        return round(self.completed_tasks / self.total_tasks * 100, 1)


class ExecutionHistoryEntry(BaseModel):
    """One row in the execution history log."""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    skipped_tasks: int
    artifacts_generated: int
    duration_seconds: float
    status: ExecutionRunStatus


class ExecutionHistory(BaseModel):
    """Append-only audit log of every execution run."""

    model_config = ConfigDict(extra="forbid")

    project_name: str
    runs: list[ExecutionHistoryEntry] = Field(default_factory=list)

    def get_next_run_id(self) -> str:
        return f"run_{len(self.runs) + 1:04d}"
