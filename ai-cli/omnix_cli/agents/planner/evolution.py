"""Task plan evolution helpers."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from omnix_cli.schemas.tasks import TaskDefinition, TaskPlan, TaskStatus


class TaskEvolutionOutcome(BaseModel):
    """Result of merging a planner proposal into existing tasks."""

    model_config = ConfigDict(extra="forbid")

    task_plan: TaskPlan
    new_task_count: int
    updated_task_count: int


def evolve_task_plan(existing: TaskPlan, proposed: TaskPlan) -> TaskEvolutionOutcome:
    """Merge a planner proposal into the existing task plan."""

    merged_tasks: list[TaskDefinition] = list(existing.tasks)
    key_to_index = {
        _task_key(task): index for index, task in enumerate(merged_tasks)
    }
    used_ids = {task.id for task in merged_tasks}
    id_remap = {task.id: task.id for task in merged_tasks}
    touched_indexes: list[int] = []
    new_task_count = 0
    updated_task_count = 0

    for proposed_task in proposed.tasks:
        key = _task_key(proposed_task)
        existing_index = key_to_index.get(key)
        if existing_index is not None:
            existing_task = merged_tasks[existing_index]
            id_remap[proposed_task.id] = existing_task.id
            updated_task = _merge_task(existing_task, proposed_task)
            if updated_task != existing_task:
                updated_task_count += 1
            merged_tasks[existing_index] = updated_task
            touched_indexes.append(existing_index)
            continue

        task_id = proposed_task.id
        if task_id in used_ids:
            task_id = _next_task_id(used_ids)
        id_remap[proposed_task.id] = task_id
        used_ids.add(task_id)

        new_task = _copy_task(proposed_task, id=task_id)
        key_to_index[_task_key(new_task)] = len(merged_tasks)
        merged_tasks.append(new_task)
        touched_indexes.append(len(merged_tasks) - 1)
        new_task_count += 1

    for index in dict.fromkeys(touched_indexes):
        task = merged_tasks[index]
        dependencies = _remap_dependencies(task.dependencies, id_remap)
        if dependencies != task.dependencies:
            merged_tasks[index] = _copy_task(task, dependencies=dependencies)

    return TaskEvolutionOutcome(
        task_plan=TaskPlan(tasks=merged_tasks),
        new_task_count=new_task_count,
        updated_task_count=updated_task_count,
    )


def _merge_task(existing: TaskDefinition, proposed: TaskDefinition) -> TaskDefinition:
    payload = existing.model_dump(mode="python")
    payload.update(
        {
            "title": proposed.title,
            "description": proposed.description or existing.description,
            "assigned_agent": proposed.assigned_agent,
            "priority": proposed.priority,
            "status": _merge_status(existing.status, proposed.status),
            "dependencies": proposed.dependencies or existing.dependencies,
            "blueprint_reference": proposed.blueprint_reference,
        }
    )
    return TaskDefinition.model_validate(payload)


def _merge_status(existing: TaskStatus, proposed: TaskStatus) -> TaskStatus:
    if existing == TaskStatus.PENDING:
        return proposed
    return existing


def _copy_task(task: TaskDefinition, **updates: object) -> TaskDefinition:
    payload = task.model_dump(mode="python")
    payload.update(updates)
    return TaskDefinition.model_validate(payload)


def _remap_dependencies(
    dependencies: list[str],
    id_remap: dict[str, str],
) -> list[str]:
    remapped_dependencies: list[str] = []
    seen: set[str] = set()
    for dependency_id in dependencies:
        remapped_id = id_remap.get(dependency_id, dependency_id)
        if remapped_id in seen:
            continue
        seen.add(remapped_id)
        remapped_dependencies.append(remapped_id)
    return remapped_dependencies


def _next_task_id(used_ids: set[str]) -> str:
    index = 1
    while True:
        task_id = f"task_{index:03d}"
        if task_id not in used_ids:
            return task_id
        index += 1


def _task_key(task: TaskDefinition) -> str:
    return _normalize_lookup(
        f"{task.assigned_agent.value}|{task.blueprint_reference}|{task.title}"
    )


def _normalize_lookup(value: str) -> str:
    return " ".join(value.casefold().split())
