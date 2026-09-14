"""`omnix chat` command."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Annotated

import typer

from omnix_cli.agents.master import MasterAgent
from omnix_cli.core.exceptions import OmnixError
from omnix_cli.core.state_manager import StateManager
from omnix_cli.memory.memory_manager import MemoryManager


def chat_command(
    message: Annotated[
        str | None,
        typer.Argument(help="Message to send to the Master Agent."),
    ] = None,
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
    """Send a message to the state-aware Master Agent."""

    state_manager = StateManager(workspace)
    memory_manager = MemoryManager(state_manager)
    master_agent = MasterAgent(memory_manager)

    user_message = message if message is not None else typer.prompt("You")

    try:
        response = asyncio.run(master_agent.handle_message(user_message))
    except ValueError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc
    except OmnixError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc

    typer.echo(response)
