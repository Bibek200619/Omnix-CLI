"""`aicli architect` command."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Annotated

import typer

from aicli.agents.architect import ArchitectAgent
from aicli.agents.architect.models import ArchitectAgentResult
from aicli.core.exceptions import AicliError
from aicli.core.state_manager import StateManager


def architect_command(
    output_json: Annotated[
        bool,
        typer.Option("--json", help="Print the Architect Agent result as JSON."),
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
    """Generate or refine the architecture blueprint."""

    state_manager = StateManager(workspace)
    architect_agent = ArchitectAgent(state_manager)

    try:
        result = asyncio.run(architect_agent.run())
    except AicliError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc

    if output_json:
        typer.echo(json.dumps(result.model_dump(mode="json"), indent=2))
        return

    typer.echo(_format_architect_result(result))


def _format_architect_result(result: ArchitectAgentResult) -> str:
    return (
        "Blueprint updated\n\n"
        f"Project Name: {result.blueprint.project_name}\n"
        f"Provider: {result.provider}\n"
        f"Model: {result.model}\n\n"
        f"Features: {result.feature_count}\n"
        f"Entities: {result.entity_count}\n"
        f"Modules: {result.module_count}\n"
        f"Architecture Notes: {result.architecture_note_count}"
    )
