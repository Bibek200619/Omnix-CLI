"""Artifact management commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from omnix_cli.core.exceptions import OmnixError
from omnix_cli.core.state_manager import StateManager


def artifacts_command(
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
    """List all generated artifacts."""

    try:
        state_manager = StateManager(workspace)
        artifacts = state_manager.list_artifacts()
    except OmnixError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc

    if not artifacts:
        typer.echo("No artifacts found.")
        return

    typer.echo(f"{'Artifact ID':<25} {'Title':<25} {'Task ID':<15} {'Agent':<12} {'Type'}")
    typer.echo("-" * 100)
    for art in artifacts:
        typer.echo(
            f"{art.id:<25} {art.title:<25} {art.task_id:<15} {art.agent:<12} {art.artifact_type}"
        )


def artifact_view_command(
    artifact_id: Annotated[str, typer.Argument(help="ID of the artifact to view.")],
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
    """View details of a specific artifact."""

    try:
        state_manager = StateManager(workspace)
        artifact = state_manager.load_artifact(artifact_id)
        if not artifact:
            typer.secho(f"Artifact '{artifact_id}' not found.", fg=typer.colors.RED, err=True)
            raise typer.Exit(1)

        typer.secho(f"Artifact: {artifact.title}", fg=typer.colors.CYAN, bold=True)
        typer.echo(f"ID:           {artifact.id}")
        typer.echo(f"Task ID:      {artifact.task_id}")
        typer.echo(f"Agent:        {artifact.agent}")
        typer.echo(f"Type:         {artifact.artifact_type}")
        typer.echo(f"Version:      {artifact.version}")
        typer.echo(f"Generated At: {artifact.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        typer.echo(f"Description:  {artifact.description}")
        
        typer.secho("\nMetadata:", fg=typer.colors.YELLOW)
        typer.echo(json.dumps(artifact.metadata, indent=2))
        
        typer.secho("\nContent:", fg=typer.colors.GREEN, bold=True)
        typer.echo("-" * 40)
        typer.echo(artifact.content)
        typer.echo("-" * 40)

    except OmnixError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc
