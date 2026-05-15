"""`aicli config` command."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from aicli.core.exceptions import AicliError, CommandUsageError
from aicli.core.state_manager import StateManager
from aicli.schemas.models import ModelsConfig
from aicli.schemas.tasks import AgentRole


def config_command(
    set_values: Annotated[
        list[str] | None,
        typer.Option(
            "--set",
            "-s",
            help=(
                "Set a role model using role=model or role=provider:model. "
                "May be repeated."
            ),
        ),
    ] = None,
    output_json: Annotated[
        bool,
        typer.Option("--json", help="Print the model configuration as JSON."),
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
    """Show or update role-to-model configuration."""

    state_manager = StateManager(workspace)

    try:
        models = state_manager.load_models()
        if set_values:
            models = _apply_model_updates(models, set_values)
            state_manager.save_models(models)
    except AicliError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc

    if output_json:
        typer.echo(json.dumps(models.legacy_model_dump(), indent=2))
        return

    typer.echo(_format_models(models))


def _apply_model_updates(models: ModelsConfig, set_values: list[str]) -> ModelsConfig:
    updated = models
    for raw_value in set_values:
        role_name, separator, model_name = raw_value.partition("=")
        if not separator:
            msg = f"Invalid --set value '{raw_value}'. Expected role=model."
            raise CommandUsageError(msg)

        try:
            role = AgentRole(role_name.strip())
        except ValueError as exc:
            allowed = ", ".join(role.value for role in AgentRole)
            msg = f"Unknown role '{role_name}'. Allowed roles: {allowed}."
            raise CommandUsageError(msg) from exc

        provider_name, parsed_model_name = _parse_assignment_value(model_name)
        if provider_name is None:
            updated = updated.with_model(role, parsed_model_name)
        else:
            updated = updated.with_assignment(
                role,
                provider=provider_name,
                model=parsed_model_name,
            )

    return updated


def _format_models(models: ModelsConfig) -> str:
    lines = ["Role models:"]
    for role in AgentRole:
        value = models.model_for(role) or "<unset>"
        lines.append(f"  {role.value:<12} {value}")
    return "\n".join(lines)


def _parse_assignment_value(value: str) -> tuple[str | None, str | None]:
    normalized_value = value.strip()
    if not normalized_value:
        return None, None

    provider_name, separator, model_name = normalized_value.partition(":")
    if separator and provider_name.strip():
        return provider_name.strip(), model_name.strip() or None

    return None, normalized_value
