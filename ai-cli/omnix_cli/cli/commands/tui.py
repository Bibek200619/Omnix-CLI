"""Launch the shared interactive terminal while retaining standalone commands."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer
from typer.core import TyperGroup


class Theme(StrEnum):
    BLACK = "black"
    BLUE = "blue"
    WHITE = "white"
    SLATE = "slate"
    LIGHT = "light"
    TERMINAL = "terminal"
    MONO = "mono"


def open_terminal(workspace: Path, theme: str = "terminal", plain: bool = False) -> None:
    from typer.main import get_command

    from omnix_cli.cli.main import app
    from omnix_cli.tui.app import launch

    command = get_command(app)
    assert isinstance(command, TyperGroup)
    launch(command, workspace, theme, plain)


def tui_command(
    workspace: Annotated[Path, typer.Option("--workspace", "-w", file_okay=False)] = Path("."),
    theme: Annotated[Theme, typer.Option(help="Terminal color theme.")] = Theme.TERMINAL,
    plain: Annotated[
        bool, typer.Option(help="Linear output without screen redraw or color.")
    ] = False,
) -> None:
    """Open the interactive terminal, or its accessible linear-output mode."""
    open_terminal(workspace, theme.value, plain)
