"""Top-level Typer app."""

from __future__ import annotations

from typing import Annotated

import typer

from omnix_cli import __version__
from omnix_cli.cli.commands.architect import architect_command
from omnix_cli.cli.commands.blueprint import blueprint_command
from omnix_cli.cli.commands.chat import chat_command
from omnix_cli.cli.commands.config import config_command
from omnix_cli.cli.commands.decisions import decisions_command
from omnix_cli.cli.commands.goals import goals_command
from omnix_cli.cli.commands.init import init_command
from omnix_cli.cli.commands.memory import memory_command
from omnix_cli.cli.commands.models import models_command
from omnix_cli.cli.commands.ping import ping_command
from omnix_cli.cli.commands.plan import plan_command
from omnix_cli.cli.commands.tasks import tasks_command
from omnix_cli.core.logging import configure_logging


def version_callback(value: bool) -> None:
    """Print the CLI version and exit."""

    if value:
        typer.echo(__version__)
        raise typer.Exit


configure_logging()

app = typer.Typer(
    name="omnix",
    help="Omnix CLI.",
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
    """Omnix CLI command group."""

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
app.command("plan")(plan_command)
app.command("tasks")(tasks_command)


if __name__ == "__main__":
    app()
