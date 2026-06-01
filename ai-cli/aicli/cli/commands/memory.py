"""`aicli memory` command."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from aicli.core.exceptions import AicliError
from aicli.core.state_manager import StateManager
from aicli.memory.memory_manager import MemoryManager
from aicli.schemas.memory import GoalStatus, ProjectMemory


def memory_command(
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
    """Display project memory summary."""

    try:
        memory = MemoryManager(StateManager(workspace)).load_memory()
    except AicliError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc

    typer.echo(_format_memory_summary(memory))


def _format_memory_summary(memory: ProjectMemory) -> str:
    active_goals = [goal for goal in memory.goals if goal.status == GoalStatus.ACTIVE]
    goal_lines = [f"* {goal.title}" for goal in active_goals] or ["None"]
    decision_titles = [decision.title for decision in memory.decisions]
    decision_titles.extend(decision.title for decision in memory.architectural_decisions)
    decision_lines = [f"* {title}" for title in decision_titles[-5:]] or ["None"]
    issue_lines = [f"* {issue.title}" for issue in memory.known_issues] or ["None"]

    return (
        "Project Goals\n\n"
        + "\n".join(goal_lines)
        + "\n\nRecent Decisions\n\n"
        + "\n".join(decision_lines)
        + "\n\nRecent Conversations\n\n"
        + f"{len(memory.conversations)} stored messages"
        + "\n\nKnown Issues\n\n"
        + "\n".join(issue_lines)
    )
