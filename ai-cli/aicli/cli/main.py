"""Top-level Typer app."""

from __future__ import annotations

from typing import Annotated

import typer

from aicli import __version__
from aicli.cli.commands.architect import architect_command
from aicli.cli.commands.blueprint import blueprint_command
from aicli.cli.commands.chat import chat_command
from aicli.cli.commands.config import config_command
from aicli.cli.commands.decisions import decisions_command
from aicli.cli.commands.goals import goals_command
from aicli.cli.commands.init import init_command
from aicli.cli.commands.memory import memory_command
from aicli.cli.commands.models import models_command
from aicli.cli.commands.ping import ping_command
from aicli.core.logging import configure_logging


def version_callback(value: bool) -> None:
    """Print the CLI version and exit."""

    if value:
        typer.echo(__version__)
        raise typer.Exit


configure_logging()

app = typer.Typer(
    name="aicli",
    help="AI Software Factory CLI.",
    no_args_is_help=True,
)


@app.callback()
def main_callback(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            help="Print the CLI version and exit.",
            callback=version_callback,
            is_eager=True,
        ),
    ] = False,
) -> None:
    """AI Software Factory command group."""

app.command("init")(init_command)
app.command("config")(config_command)
app.command("chat")(chat_command)
app.command("architect")(architect_command)
app.command("blueprint")(blueprint_command)
app.command("models")(models_command)
app.command("ping")(ping_command)
app.command("memory")(memory_command)
app.command("goals")(goals_command)
app.command("decisions")(decisions_command)


if __name__ == "__main__":
    app()
