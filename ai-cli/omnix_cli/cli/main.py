"""Top-level Typer app."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated

import typer

from omnix_cli import __version__
from omnix_cli.cli.commands.architect import architect_command
from omnix_cli.cli.commands.artifacts import artifact_view_command, artifacts_command
from omnix_cli.cli.commands.blueprint import blueprint_command
from omnix_cli.cli.commands.build import (
    build_command,
    build_status_command,
    builds_command,
)
from omnix_cli.cli.commands.chat import chat_command
from omnix_cli.cli.commands.config import config_command
from omnix_cli.cli.commands.decisions import decisions_command
from omnix_cli.cli.commands.execute import execute_command
from omnix_cli.cli.commands.execute_all import execute_all_command, execution_command
from omnix_cli.cli.commands.goals import goals_command
from omnix_cli.cli.commands.init import init_command
from omnix_cli.cli.commands.integration import integrate_command, integration_summary_command
from omnix_cli.cli.commands.memory import memory_command
from omnix_cli.cli.commands.models import models_command
from omnix_cli.cli.commands.omnix_account import (
    link_command,
    login_command,
    logout_command,
    omnix_status_command,
    unlink_command,
)
from omnix_cli.cli.commands.ping import ping_command
from omnix_cli.cli.commands.plan import plan_command
from omnix_cli.cli.commands.qa import qa_command, quality_command
from omnix_cli.cli.commands.repair import repair_command, repairs_command
from omnix_cli.cli.commands.tasks import tasks_command
from omnix_cli.cli.commands.tui import Theme, open_terminal, tui_command
from omnix_cli.core.logging import configure_logging
from omnix_cli.integrations.omnix_sessions import (
    history_sessions_command,
    work_sessions_command,
)


def version_callback(value: bool) -> None:
    """Print the CLI version and exit."""

    if value:
        typer.echo(__version__)
        raise typer.Exit


configure_logging()

app = typer.Typer(
    name="omnix",
    help="Omnix CLI.",
    no_args_is_help=False,
    invoke_without_command=True,
)


@app.callback()
def main_callback(
    ctx: typer.Context,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            help="Print the CLI version and exit.",
            callback=version_callback,
            is_eager=True,
        ),
    ] = False,
    workspace: Annotated[
        Path, typer.Option("--workspace", "-w", file_okay=False, help="Interactive workspace.")
    ] = Path("."),
    plain: Annotated[
        bool, typer.Option(help="Start an interactive session with linear output.")
    ] = False,
    theme: Annotated[Theme, typer.Option(help="Interactive terminal theme.")] = Theme.TERMINAL,
) -> None:
    """Omnix CLI command group."""
    if ctx.invoked_subcommand is None:
        if plain or (sys.stdin.isatty() and sys.stdout.isatty()):
            open_terminal(workspace, theme.value, plain)
        else:
            typer.echo(ctx.get_help())


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
app.command("execute")(execute_command)
app.command("execute-all")(execute_all_command)
app.command("execution")(execution_command)
app.command("integrate")(integrate_command)
app.command("integration")(integration_summary_command)
app.command("qa")(qa_command)
app.command("quality")(quality_command)
app.command("repair")(repair_command)
app.command("repairs")(repairs_command)
app.command("artifacts")(artifacts_command)
app.command("artifact")(artifact_view_command)
app.command("build")(build_command)
app.command("build-status")(build_status_command)
app.command("builds")(builds_command)
app.command("login")(login_command)
app.command("logout")(logout_command)
sessions_app = typer.Typer(help="Poll and run explicitly approved Omnix capability sessions.")
sessions_app.command("work")(work_sessions_command)
sessions_app.command("history")(history_sessions_command)
app.add_typer(sessions_app, name="sessions")
app.command("link")(link_command)
app.command("unlink")(unlink_command)
app.command("status")(omnix_status_command)
app.command("tui")(tui_command)


if __name__ == "__main__":
    app()
