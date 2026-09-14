"""`omnix models` command."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from omnix_cli.core.exceptions import OmnixError
from omnix_cli.core.state_manager import StateManager
from omnix_cli.schemas.models import ModelsConfig
from omnix_cli.schemas.tasks import AgentRole


def models_command(
    output_json: Annotated[
        bool,
        typer.Option("--json", help="Print provider/model assignments as JSON."),
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
    """Display role-to-provider/model assignments."""

    state_manager = StateManager(workspace)

    try:
        models = state_manager.load_models()
    except OmnixError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc

    if output_json:
        typer.echo(json.dumps(models.model_dump(mode="json"), indent=2))
        return

    typer.echo(_format_provider_models(models))


def _format_provider_models(models: ModelsConfig) -> str:
    sections: list[str] = []
    for role in AgentRole:
        assignment = models.assignment_for(role)
        provider_name = assignment.provider if assignment and assignment.provider else "<unset>"
        model_name = assignment.model if assignment and assignment.model else "<unset>"
        sections.append(f"{role.value}\nprovider: {provider_name}\nmodel: {model_name}")
    return "\n\n".join(sections)
