"""`omnix tasks` command."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from omnix_cli.core.exceptions import OmnixError
from omnix_cli.core.state_manager import StateManager
from omnix_cli.schemas.tasks import TaskDefinition, TaskPlan


def tasks_command(
    output_json: Annotated[
        bool,
        typer.Option("--json", help="Print the current task plan as JSON."),
    ] = False,
    workspace: Annotated[
        Path,
        typer.Option(
            "--workspace",
            "-w",
            help="Project root containing the .project directory.",
            file_okay=False,
        ),
    ] = Path("."),
) -> None:
    """Display the current project task plan."""

    try:
        task_plan = StateManager(workspace).load_tasks()
    except OmnixError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc

    if output_json:
        typer.echo(json.dumps(task_plan.model_dump(mode="json"), indent=2))
        return

    typer.echo(_format_tasks(task_plan))


def _format_tasks(task_plan: TaskPlan) -> str:
    if not task_plan.tasks:
        return "Tasks\nNone"

    title_by_id = {task.id: task.title for task in task_plan.tasks}
    sections = [_format_task(task, title_by_id) for task in task_plan.tasks]
    return "Task List\n\n" + "\n\n".join(sections)


def _format_task(task: TaskDefinition, title_by_id: dict[str, str]) -> str:
    lines = [
        f"[{task.priority.value.upper()}] [{task.status.value.upper()}] {task.title}",
        f"Agent: {task.assigned_agent.value}",
    ]
    if task.dependencies:
        dependencies = ", ".join(
            title_by_id.get(dependency_id, dependency_id)
            for dependency_id in task.dependencies
        )
        lines.append(f"Depends On: {dependencies}")
    lines.append(f"Blueprint: {task.blueprint_reference}")
    return "\n".join(lines)
