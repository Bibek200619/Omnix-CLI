"""`aicli blueprint` command."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Annotated, Protocol

import typer

from aicli.core.exceptions import AicliError
from aicli.core.state_manager import StateManager
from aicli.schemas.blueprint import ArchitectureNote, GoalDefinition, ProjectBlueprint


class NamedBlueprintItem(Protocol):
    """Shared display contract for named blueprint sections."""

    name: str
    description: str


def blueprint_command(
    output_json: Annotated[
        bool,
        typer.Option("--json", help="Print the current blueprint as JSON."),
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
    """Display the current architecture blueprint."""

    try:
        blueprint = StateManager(workspace).load_blueprint()
    except AicliError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc

    if output_json:
        typer.echo(json.dumps(blueprint.model_dump(mode="json"), indent=2))
        return

    typer.echo(_format_blueprint(blueprint))


def _format_blueprint(blueprint: ProjectBlueprint) -> str:
    return "\n\n".join(
        [
            "Project Blueprint",
            f"Project Name\n{blueprint.project_name or '<unset>'}",
            f"Description\n{blueprint.description or '<unset>'}",
            _format_goals(blueprint.goals),
            _format_named_section("Pages", blueprint.pages),
            _format_named_section("Features", blueprint.features),
            _format_named_section("Entities", blueprint.entities),
            _format_named_section("Modules", blueprint.modules),
            _format_architecture_notes(blueprint.architecture_notes),
        ]
    )


def _format_goals(goals: Sequence[GoalDefinition]) -> str:
    if not goals:
        return "Goals\nNone"

    lines = [
        _format_line(goal.title, goal.description)
        for goal in goals
    ]
    return "Goals\n" + "\n".join(lines)


def _format_named_section(
    title: str,
    items: Sequence[NamedBlueprintItem],
) -> str:
    if not items:
        return f"{title}\nNone"

    lines = [_format_line(item.name, item.description) for item in items]
    return f"{title}\n" + "\n".join(lines)


def _format_architecture_notes(notes: Sequence[ArchitectureNote]) -> str:
    if not notes:
        return "Architecture Notes\nNone"

    lines = [
        _format_line(note.title, note.content) if note.title else f"* {note.content}"
        for note in notes
    ]
    return "Architecture Notes\n" + "\n".join(lines)


def _format_line(name: str, description: str) -> str:
    if description:
        return f"* {name}: {description}"
    return f"* {name}"
