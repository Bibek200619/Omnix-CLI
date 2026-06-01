"""`aicli decisions` command."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from aicli.core.exceptions import AicliError
from aicli.core.state_manager import StateManager
from aicli.memory.memory_manager import MemoryManager


def decisions_command(
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
    """Display stored project decisions."""

    try:
        memory = MemoryManager(StateManager(workspace)).load_memory()
    except AicliError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc

    decision_titles = [decision.title for decision in memory.decisions]
    decision_titles.extend(decision.title for decision in memory.architectural_decisions)
    typer.echo(_format_decisions(decision_titles))


def _format_decisions(decision_titles: list[str]) -> str:
    if not decision_titles:
        return "Project Decisions\n\nNone"

    lines = [f"* {decision}" for decision in decision_titles]
    return "Project Decisions\n\n" + "\n".join(lines)
