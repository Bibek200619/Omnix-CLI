"""DAG builder and topological-sort batcher for task dependency analysis."""

from __future__ import annotations

from collections import deque

from omnix_cli.core.exceptions import CyclicDependencyError, ExecutionPlanError
from omnix_cli.schemas.execution import ExecutionBatch
from omnix_cli.schemas.tasks import TaskDefinition


def build_execution_batches(tasks: list[TaskDefinition]) -> list[ExecutionBatch]:
    """Analyse task dependencies, validate the DAG, and return ordered batches.

    Tasks with no unresolved dependencies are placed in the same batch and can
    run concurrently.  Batches themselves are ordered sequentially so that a
    task's dependencies are always satisfied before it starts.

    Raises:
        ExecutionPlanError: if a dependency references a task ID that does not
            exist in ``tasks``.
        CyclicDependencyError: if the dependency graph contains a cycle.
    """
    task_ids = {t.id for t in tasks}

    # Validate that all declared dependency IDs exist
    for task in tasks:
        for dep_id in task.dependencies:
            if dep_id not in task_ids:
                msg = (
                    f"Task '{task.id}' declares dependency '{dep_id}' "
                    "which does not exist in the task plan."
                )
                raise ExecutionPlanError(msg)

    # Build adjacency structures for Kahn's algorithm (BFS topological sort)
    # in_degree[task_id] = number of unresolved prerequisites
    in_degree: dict[str, int] = {t.id: 0 for t in tasks}
    # dependents[dep_id] = list of task IDs that depend on dep_id
    dependents: dict[str, list[str]] = {t.id: [] for t in tasks}

    for task in tasks:
        in_degree[task.id] = len(task.dependencies)
        for dep_id in task.dependencies:
            dependents[dep_id].append(task.id)

    # Kahn's BFS — produces level-by-level batches
    batches: list[ExecutionBatch] = []
    queue: deque[str] = deque(
        tid for tid, deg in in_degree.items() if deg == 0
    )
    processed = 0

    while queue:
        # Everything currently in the queue is independent → one batch
        batch_task_ids = list(queue)
        queue.clear()

        batches.append(
            ExecutionBatch(batch_index=len(batches), task_ids=batch_task_ids)
        )
        processed += len(batch_task_ids)

        # Decrement in-degree for tasks that depended on just-processed ones
        next_ready: list[str] = []
        for tid in batch_task_ids:
            for dependent_id in dependents[tid]:
                in_degree[dependent_id] -= 1
                if in_degree[dependent_id] == 0:
                    next_ready.append(dependent_id)

        for tid in next_ready:
            queue.append(tid)

    if processed != len(tasks):
        # Not all tasks were processed → cycle exists
        cycle_members = [tid for tid, deg in in_degree.items() if deg > 0]
        msg = (
            f"Cyclic dependency detected among tasks: {cycle_members}. "
            "Cannot build a valid execution plan."
        )
        raise CyclicDependencyError(msg)

    return batches


def build_dependency_map(tasks: list[TaskDefinition]) -> dict[str, list[str]]:
    """Return a mapping of task_id → list of dependency task IDs."""
    return {t.id: list(t.dependencies) for t in tasks}


def build_agent_map(tasks: list[TaskDefinition]) -> dict[str, str]:
    """Return a mapping of task_id → assigned agent name."""
    return {t.id: t.assigned_agent.value for t in tasks}
