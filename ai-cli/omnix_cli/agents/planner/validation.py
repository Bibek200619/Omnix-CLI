"""Task plan validation for Phase 4 planning workflows."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from omnix_cli.core.exceptions import TaskValidationError
from omnix_cli.schemas.tasks import TaskPlan


class TaskValidationResult(BaseModel):
    """Structured result for task plan validation."""

    model_config = ConfigDict(extra="forbid")

    valid: bool
    errors: list[str] = Field(default_factory=list)


def collect_task_validation_errors(
    task_plan: TaskPlan,
    *,
    require_tasks: bool = True,
) -> list[str]:
    """Return clear validation errors for a task plan."""

    errors: list[str] = []
    if require_tasks and not task_plan.tasks:
        errors.append("at least one task is required.")

    task_ids = [task.id for task in task_plan.tasks]
    duplicate_ids = sorted({task_id for task_id in task_ids if task_ids.count(task_id) > 1})
    for duplicate_id in duplicate_ids:
        errors.append(f"duplicate task id '{duplicate_id}'.")

    known_ids = set(task_ids)
    for task in task_plan.tasks:
        if not task.blueprint_reference.strip():
            errors.append(f"task '{task.id}' is missing blueprint_reference.")
        for dependency_id in task.dependencies:
            if dependency_id == task.id:
                errors.append(f"task '{task.id}' cannot depend on itself.")
            elif dependency_id not in known_ids:
                errors.append(
                    f"task '{task.id}' depends on unknown task id '{dependency_id}'."
                )

    return errors


def validate_task_plan(
    task_plan: TaskPlan,
    *,
    require_tasks: bool = True,
) -> TaskValidationResult:
    """Validate that a task plan is complete enough to persist."""

    errors = collect_task_validation_errors(task_plan, require_tasks=require_tasks)
    result = TaskValidationResult(valid=not errors, errors=errors)
    if errors:
        formatted_errors = "\n".join(f"- {error}" for error in errors)
        msg = f"Invalid task plan:\n{formatted_errors}"
        raise TaskValidationError(msg)
    return result
