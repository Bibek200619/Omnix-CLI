"""`omnix integrate` and `omnix integration` commands."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Annotated

import typer

from omnix_cli.agents.integration.agent import IntegrationAgent
from omnix_cli.core.exceptions import OmnixError
from omnix_cli.core.state_manager import StateManager


def integrate_command(
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
    """Analyze worker artifacts and assemble the Integrated Package."""

    async def _run() -> None:
        state_manager = StateManager(workspace)
        try:
            typer.echo("Integrating project artifacts...")
            agent = IntegrationAgent(state_manager)
            result = await agent.integrate()
            
            typer.secho("\nIntegration Successful!", fg=typer.colors.GREEN, bold=True)
            typer.echo(
                f"Integrated Package:  {result.package.project_name} ({result.package.version})"
            )
            typer.echo(f"Artifacts Processed: {result.integration_report.artifacts_processed}")
            typer.echo(f"Dependencies Found:  {result.integration_report.dependencies_found}")
            
            if result.integration_report.conflicts_found > 0:
                typer.secho(
                    f"Conflicts Detected:  {result.integration_report.conflicts_found}",
                    fg=typer.colors.YELLOW,
                )
            else:
                typer.echo("Conflicts Detected:  0")
                
            typer.echo(f"Coverage Status:     {result.integration_report.coverage_status}")
            typer.echo("\nOutputs saved to .project/integration/")
        except OmnixError as exc:
            typer.secho(str(exc), fg=typer.colors.RED, err=True)
            raise typer.Exit(1) from exc
        except Exception as exc:
            typer.secho(f"Unexpected error: {exc}", fg=typer.colors.RED, err=True)
            raise typer.Exit(1) from exc

    asyncio.run(_run())


def integration_summary_command(
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
    """Display the summary of the current integration state."""

    state_manager = StateManager(workspace)
    try:
        report = state_manager.load_integration_report()
        package = state_manager.load_integrated_package()
        
        typer.secho(f"Integration Summary: {report.project_name}", bold=True)
        typer.echo("-" * 40)
        typer.echo(f"Status:             {report.status}")
        typer.echo(f"Last Integrated:    {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        typer.echo(f"Artifacts:          {report.artifacts_processed}")
        
        for agent, count in report.artifacts_by_agent.items():
            typer.echo(f"  - {agent:10}: {count}")
            
        typer.echo(f"Dependencies:       {report.dependencies_found}")
        
        color = typer.colors.GREEN if report.conflicts_found == 0 else typer.colors.YELLOW
        typer.secho(f"Conflicts:          {report.conflicts_found}", fg=color)
        
        typer.echo(f"Coverage Status:    {report.coverage_status}")
        
        if package.coverage.gaps:
            typer.echo("\nCoverage Gaps:")
            for gap in package.coverage.gaps:
                typer.echo(f"  [!] {gap}")
                
        if package.conflicts:
            typer.echo("\nTop Conflicts:")
            for conflict in package.conflicts[:5]:
                typer.echo(f"  - [{conflict.severity.upper()}] {conflict.title}")

    except OmnixError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc
