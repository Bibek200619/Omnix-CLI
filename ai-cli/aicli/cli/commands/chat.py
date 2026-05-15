"""`aicli chat` command."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Annotated

import typer

from aicli.agents.master import MasterAgent
from aicli.core.exceptions import AicliError
from aicli.core.state_manager import StateManager
from aicli.memory.memory_manager import MemoryManager


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
    """Send a message to the Phase 0 Master Agent."""

    state_manager = StateManager(workspace)
    memory_manager = MemoryManager(state_manager)
    master_agent = MasterAgent(memory_manager)

    user_message = message if message is not None else typer.prompt("You")

    try:
        response = asyncio.run(master_agent.handle_message(user_message))
    except ValueError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc
    except AicliError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc

    typer.echo(response)
