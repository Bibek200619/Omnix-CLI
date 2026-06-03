"""`omnix repair` and `omnix repairs` commands."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Annotated

import typer

from omnix_cli.agents.repair.agent import RepairAgent
from omnix_cli.core.exceptions import OmnixError
from omnix_cli.core.state_manager import StateManager


def repair_command(
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
    """Generate repair plans and artifacts from QA findings."""

    async def _run() -> None:
        state_manager = StateManager(workspace)
        try:
            typer.echo("Loading QA reports...")
            agent = RepairAgent(state_manager)

            typer.echo("Generating repair plan and artifacts...")
            result = await agent.repair()

            plan = result.repair_plan
            report = result.repair_report

            typer.secho(
                f"\nRepair Cycle #{result.cycle} Complete!", fg=typer.colors.GREEN, bold=True
            )
            typer.echo(f"Issues Processed:        {report.issues_processed}")

            # Severity breakdown
            if report.critical_count:
                typer.secho(
                    f"  Critical:              {report.critical_count}", fg=typer.colors.RED
                )
            if report.high_count:
                typer.secho(
                    f"  High:                  {report.high_count}", fg=typer.colors.YELLOW
                )
            if report.medium_count:
                typer.echo(f"  Medium:                {report.medium_count}")
            if report.low_count:
                typer.echo(f"  Low:                   {report.low_count}")

            typer.echo(f"Repair Artifacts Generated: {report.artifacts_generated}")

            if report.expected_impact:
                typer.echo(f"\nExpected Impact:\n  {report.expected_impact}")

            typer.echo("\nRepair Plan Summary:")
            for item in plan.items:
                severity_color = {
                    "critical": typer.colors.RED,
                    "high": typer.colors.YELLOW,
                    "medium": typer.colors.WHITE,
                    "low": typer.colors.BRIGHT_BLACK,
                }.get(item.severity, typer.colors.WHITE)
                typer.secho(
                    f"  [{item.severity.upper():8s}] {item.id}: {item.issue}",
                    fg=severity_color,
                )

            typer.secho(f"\nStatus: {report.status}", fg=typer.colors.GREEN, bold=True)
            typer.echo("Outputs saved to .project/repair/")

        except OmnixError as exc:
            typer.secho(str(exc), fg=typer.colors.RED, err=True)
            raise typer.Exit(1) from exc
        except Exception as exc:
            typer.secho(f"Unexpected error: {exc}", fg=typer.colors.RED, err=True)
            raise typer.Exit(1) from exc

    asyncio.run(_run())


def repairs_command(
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
    """Display repair history, statistics, and cycle summaries."""

    state_manager = StateManager(workspace)
    try:
        history = state_manager.load_repair_history()

        typer.secho(
            f"Repair History: {history.project_name}", bold=True
        )
        typer.echo("-" * 50)
        typer.echo(f"Total Repair Cycles: {len(history.cycles)}")

        if not history.cycles:
            typer.echo("No repair cycles recorded yet. Run 'omnix repair' first.")
            return

        total_issues = sum(c.issues_addressed for c in history.cycles)
        total_artifacts = sum(c.artifacts_generated for c in history.cycles)
        typer.echo(f"Total Issues Addressed:  {total_issues}")
        typer.echo(f"Total Artifacts Generated: {total_artifacts}")

        typer.echo("\nCycle History:")
        header = (
            f"  {'Cycle':>5}  {'Timestamp':>20}  {'Issues':>6}"
            f"  {'Artifacts':>9}  {'Score Before':>12}  {'Status'}"
        )
        typer.echo(header)
        typer.echo(f"  {'-'*5}  {'-'*20}  {'-'*6}  {'-'*9}  {'-'*12}  {'-'*8}")
        for entry in history.cycles:
            ts = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            typer.echo(
                f"  {entry.cycle:>5}  {ts:>20}  {entry.issues_addressed:>6}"
                f"  {entry.artifacts_generated:>9}"
                f"  {entry.quality_score_before:>12}  {entry.status}"
            )

        # Show latest report
        try:
            report = state_manager.load_repair_report()
            typer.echo(f"\nLatest Repair Report (Cycle #{report.cycle}):")
            typer.echo(f"  Artifacts Generated: {report.artifacts_generated}")
            typer.echo(f"  Status:              {report.status}")
            if report.expected_impact:
                typer.echo(f"  Expected Impact:     {report.expected_impact}")
        except OmnixError:
            pass

    except OmnixError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc
