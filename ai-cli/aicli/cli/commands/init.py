"""`aicli init` command."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from aicli.core.exceptions import AicliError
from aicli.core.state_manager import StateManager


def init_command(
    project_name: Annotated[
        str,
        typer.Option("--project-name", "-n", help="Project name stored in the blueprint."),
    ] = "",
    description: Annotated[
        str,
        typer.Option("--description", "-d", help="Project description stored in the blueprint."),
    ] = "",
    force: Annotated[
        bool,
        typer.Option("--force", help="Overwrite existing Phase 0 project state files."),
    ] = False,
    workspace: Annotated[
        Path,
        typer.Option(
            "--workspace",
            "-w",
            help="Project root where .project will be created.",
            file_okay=False,
        ),
    ] = Path("."),
) -> None:
    """Initialize validated AI Software Factory project metadata."""

    state_manager = StateManager(workspace)

    try:
        state_manager.init_project(
            project_name=project_name,
            description=description,
            force=force,
        )
    except AicliError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc

    typer.echo(f"Initialized AI Software Factory project at {state_manager.project_dir}")
