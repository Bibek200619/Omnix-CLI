"""`omnix ping` command."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import typer

from omnix_cli.core.exceptions import CommandUsageError, OmnixError
from omnix_cli.core.settings import Settings
from omnix_cli.core.state_manager import StateManager
from omnix_cli.providers.exceptions import ProviderConfigurationError
from omnix_cli.providers.registry import ProviderRegistry, build_default_provider_registry
from omnix_cli.schemas.tasks import AgentRole


@dataclass(frozen=True, slots=True)
class PingResult:
    """Result of a provider ping."""

    role: AgentRole
    provider: str
    model: str
    response: str


def ping_command(
    role_name: Annotated[str, typer.Argument(help="Agent role to ping.")],
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
    """Send a test prompt through the configured provider for a role."""

    try:
        role = _parse_role(role_name)
        state_manager = StateManager(workspace)
        settings = Settings()
        registry = build_default_provider_registry(settings)
        result = asyncio.run(ping_role(role, state_manager, registry))
    except OmnixError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc

    typer.echo(_format_ping_result(result))


async def ping_role(
    role: AgentRole,
    state_manager: StateManager,
    registry: ProviderRegistry,
) -> PingResult:
    """Run the provider-layer ping for a role."""

    models = state_manager.load_models()
    assignment = models.assignment_for(role)
    if assignment is None or assignment.provider is None or assignment.model is None:
        msg = (
            f"Role '{role.value}' is missing provider/model configuration. "
            "Use `omnix config --set role=provider:model` first."
        )
        raise ProviderConfigurationError(msg)

    provider = registry.create(assignment.provider, model=assignment.model)
    response = await provider.generate(
        "Reply with a short provider connectivity confirmation.",
        system_prompt=(
            "You are handling an Omnix CLI provider-layer ping. "
            "Return a concise plain-text confirmation."
        ),
    )
    return PingResult(
        role=role,
        provider=provider.provider_name,
        model=provider.model,
        response=response,
    )


def _parse_role(role_name: str) -> AgentRole:
    try:
        return AgentRole(role_name.strip())
    except ValueError as exc:
        allowed = ", ".join(role.value for role in AgentRole)
        msg = f"Unknown role '{role_name}'. Allowed roles: {allowed}."
        raise CommandUsageError(msg) from exc


def _format_ping_result(result: PingResult) -> str:
    return (
        f"Role: {result.role.value}\n"
        f"Provider: {result.provider}\n"
        f"Model: {result.model}\n\n"
        f"Response:\n{result.response}"
    )
