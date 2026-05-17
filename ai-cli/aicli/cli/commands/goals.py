"""`aicli goals` command."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from aicli.core.exceptions import AicliError
from aicli.core.state_manager import StateManager
from aicli.memory.memory_manager import MemoryManager
from aicli.schemas.memory import GoalStatus, ProjectGoal


def goals_command(
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
    """Display stored project goals."""

    try:
        goals = MemoryManager(StateManager(workspace)).get_goals(GoalStatus.ACTIVE)
    except AicliError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc

    typer.echo(_format_goals(goals))


def _format_goals(goals: list[ProjectGoal]) -> str:
    if not goals:
        return "Active Goals\n\nNone"

    lines = [f"{index}. {goal.title}" for index, goal in enumerate(goals, start=1)]
    return "Active Goals\n\n" + "\n".join(lines)
