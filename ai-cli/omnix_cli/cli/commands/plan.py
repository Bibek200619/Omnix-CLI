"""`omnix plan` command."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Annotated

import typer

from omnix_cli.agents.planner import PlannerAgent
from omnix_cli.agents.planner.models import PlannerAgentResult
from omnix_cli.core.exceptions import OmnixError
from omnix_cli.core.state_manager import StateManager
from omnix_cli.schemas.tasks import TaskAssignedAgent


def plan_command(
    output_json: Annotated[
        bool,
        typer.Option("--json", help="Print the Planner Agent result as JSON."),
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
    """Generate or refine the project task plan."""

    state_manager = StateManager(workspace)
    planner_agent = PlannerAgent(state_manager)

    try:
        result = asyncio.run(planner_agent.run())
    except OmnixError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc

    if output_json:
        typer.echo(json.dumps(result.model_dump(mode="json"), indent=2))
        return

    typer.echo(_format_planner_result(result))


def _format_planner_result(result: PlannerAgentResult) -> str:
    lines = [
        f"Tasks Generated: {result.new_task_count}",
        f"Total Tasks: {result.task_count}",
    ]
    if result.updated_task_count:
        lines.append(f"Updated Tasks: {result.updated_task_count}")

    lines.append("")
    for agent in TaskAssignedAgent:
        count = result.tasks_by_agent.get(agent.value, 0)
        if count:
            lines.append(f"{agent.value.title()}: {count}")

    return "\n".join(lines)
