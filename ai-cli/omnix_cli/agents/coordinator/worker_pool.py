"""Async worker pool: dispatches individual tasks to their assigned worker agents."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Protocol

from omnix_cli.schemas.artifacts import Artifact
from omnix_cli.schemas.execution import TaskExecutionResult, TaskExecutionStatus
from omnix_cli.schemas.tasks import TaskDefinition


class WorkerAgent(Protocol):
    """Minimal interface every worker agent must satisfy."""

    async def execute_task(self, task: TaskDefinition) -> object:
        """Execute the task and return an agent result with an ``artifact`` field."""
        ...


class WorkerPool:
    """Dispatches tasks to registered worker agents and collects results.

    Workers are injected at construction time to keep this class testable
    without any I/O or provider calls.
    """

    def __init__(self, workers: dict[str, WorkerAgent]) -> None:
        """
        Args:
            workers: Mapping of agent-name (e.g. "backend") → worker instance.
        """
        self._workers = workers

    async def run_task(self, task: TaskDefinition) -> TaskExecutionResult:
        """Execute one task, returning a structured result regardless of outcome."""

        agent_name = task.assigned_agent.value
        started_at = datetime.now()

        worker = self._workers.get(agent_name)
        if worker is None:
            finished_at = datetime.now()
            return TaskExecutionResult(
                task_id=task.id,
                task_title=task.title,
                assigned_agent=agent_name,
                status=TaskExecutionStatus.SKIPPED,
                error=f"No worker registered for agent '{agent_name}'.",
                started_at=started_at,
                finished_at=finished_at,
                duration_seconds=(finished_at - started_at).total_seconds(),
            )

        try:
            agent_result = await worker.execute_task(task)
            finished_at = datetime.now()

            # Extract artifact if present (duck-typed — all worker agents expose .artifact)
            artifact: Artifact | None = getattr(agent_result, "artifact", None)

            return TaskExecutionResult(
                task_id=task.id,
                task_title=task.title,
                assigned_agent=agent_name,
                status=TaskExecutionStatus.COMPLETED,
                artifact_id=artifact.id if artifact else None,
                started_at=started_at,
                finished_at=finished_at,
                duration_seconds=(finished_at - started_at).total_seconds(),
            )

        except Exception as exc:  # noqa: BLE001
            finished_at = datetime.now()
            return TaskExecutionResult(
                task_id=task.id,
                task_title=task.title,
                assigned_agent=agent_name,
                status=TaskExecutionStatus.FAILED,
                error=str(exc),
                started_at=started_at,
                finished_at=finished_at,
                duration_seconds=(finished_at - started_at).total_seconds(),
            )

    async def run_batch(
        self, tasks: list[TaskDefinition]
    ) -> list[TaskExecutionResult]:
        """Execute all tasks in the batch concurrently and collect results."""
        return list(await asyncio.gather(*(self.run_task(t) for t in tasks)))
