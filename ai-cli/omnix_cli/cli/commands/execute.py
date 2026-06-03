"""`omnix execute` command."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Annotated

import typer

from omnix_cli.agents.frontend.agent import FrontendAgent
from omnix_cli.core.exceptions import OmnixError
from omnix_cli.core.state_manager import StateManager
from omnix_cli.schemas.tasks import AgentRole


def execute_command(
    task_id: Annotated[str, typer.Argument(help="ID of the task to execute.")],
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
    """Execute a task using the assigned worker agent."""

    async def _run() -> None:
        state_manager = StateManager(workspace)
        try:
            task_plan = state_manager.load_tasks()
        except OmnixError as exc:
            typer.secho(str(exc), fg=typer.colors.RED, err=True)
            raise typer.Exit(1) from exc

        # Find the task
        task = next((t for t in task_plan.tasks if t.id == task_id), None)
        if not task:
            typer.secho(f"Task '{task_id}' not found.", fg=typer.colors.RED, err=True)
            raise typer.Exit(1)
        
        if task.assigned_agent.value != AgentRole.FRONTEND.value:
            typer.secho(
                f"Agent '{task.assigned_agent}' is not yet supported for execution. "
                "Only 'frontend' tasks can be executed in Phase 5A.",
                fg=typer.colors.YELLOW,
                err=True,
            )
            raise typer.Exit(0)

        try:
            typer.echo(f"Executing task '{task.title}' ({task_id}) using Frontend Agent...")
            
            agent = FrontendAgent(state_manager)
            result = await agent.execute_task(task)
            
            typer.secho("\nArtifact Generated Successfully!", fg=typer.colors.GREEN, bold=True)
            typer.echo(f"Artifact ID:   {result.artifact.id}")
            typer.echo(f"Title:         {result.artifact.title}")
            typer.echo(f"Type:          {result.artifact.artifact_type}")
            typer.echo(f"Version:       {result.artifact.version}")
            typer.echo(f"Provider:      {result.provider} ({result.model})")
            typer.echo(f"\nArtifact saved to .project/artifacts/{result.artifact.id}.json")
        except OmnixError as exc:
            typer.secho(str(exc), fg=typer.colors.RED, err=True)
            raise typer.Exit(1) from exc
        except Exception as exc:
            typer.secho(f"Unexpected error: {exc}", fg=typer.colors.RED, err=True)
            raise typer.Exit(1) from exc

    asyncio.run(_run())
