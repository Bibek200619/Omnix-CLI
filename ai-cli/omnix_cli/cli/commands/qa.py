"""`omnix qa` and `omnix quality` commands."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Annotated

import typer

from omnix_cli.agents.qa.agent import QAAgent
from omnix_cli.core.exceptions import OmnixError
from omnix_cli.core.state_manager import StateManager


def qa_command(
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
    """Evaluate project quality and generate reports."""

    async def _run() -> None:
        state_manager = StateManager(workspace)
        try:
            typer.echo("Running QA analysis...")
            agent = QAAgent(state_manager)
            result = await agent.evaluate()
            
            typer.secho("\nQA Analysis Complete!", fg=typer.colors.GREEN, bold=True)
            typer.echo(f"Quality Score:    {result.summary.quality_score}")
            typer.echo(f"Coverage Score:   {result.summary.coverage_score}%")
            
            color = typer.colors.GREEN
            if result.summary.critical_issues > 0:
                color = typer.colors.RED
            elif result.summary.high_issues > 0:
                color = typer.colors.YELLOW
                
            typer.secho(f"Critical Issues:  {result.summary.critical_issues}", fg=color)
            typer.echo(f"High Issues:      {result.summary.high_issues}")
            typer.echo(f"Medium Issues:    {result.summary.medium_issues}")
            typer.echo(f"Low Issues:       {result.summary.low_issues}")
            
            status_color = typer.colors.GREEN
            if result.summary.status in ["FAILED", "REVIEW_REQUIRED"]:
                status_color = (
                    typer.colors.RED
                    if result.summary.status == "FAILED"
                    else typer.colors.YELLOW
                )

            typer.secho(f"\nStatus:           {result.summary.status}", fg=status_color, bold=True)
            typer.echo("\nReports saved to .project/qa/")
            
        except OmnixError as exc:
            typer.secho(str(exc), fg=typer.colors.RED, err=True)
            raise typer.Exit(1) from exc
        except Exception as exc:
            typer.secho(f"Unexpected error: {exc}", fg=typer.colors.RED, err=True)
            raise typer.Exit(1) from exc

    asyncio.run(_run())


def quality_command(
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
    """Display the summary of the current quality state."""

    state_manager = StateManager(workspace)
    try:
        summary = state_manager.load_qa_summary()
        report = state_manager.load_quality_report()
        
        typer.secho(f"Quality Summary: {summary.project_name}", bold=True)
        typer.echo("-" * 40)
        typer.echo(f"Quality Score:      {summary.quality_score}")
        typer.echo(f"Coverage Score:     {summary.coverage_score}%")
        typer.echo(f"Status:             {summary.status}")
        typer.echo(f"Last QA Run:        {summary.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        
        typer.echo("\nFindings Summary:")
        typer.echo(f"  Critical: {summary.critical_issues}")
        typer.echo(f"  High:     {summary.high_issues}")
        typer.echo(f"  Medium:   {summary.medium_issues}")
        typer.echo(f"  Low:      {summary.low_issues}")
        
        if report.findings:
            typer.echo("\nTop Findings:")
            for finding in report.findings[:5]:
                typer.echo(f"  - [{finding.severity.upper()}] {finding.title}")

    except OmnixError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc
