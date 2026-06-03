"""`omnix execute-all` and `omnix execution` commands."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Annotated

import typer

from omnix_cli.agents.coordinator.coordinator import ExecutionCoordinator
from omnix_cli.core.exceptions import CyclicDependencyError, ExecutionPlanError, OmnixError
from omnix_cli.core.state_manager import StateManager
from omnix_cli.schemas.execution import ExecutionRunStatus, TaskExecutionStatus


def execute_all_command(
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
    """Execute all tasks in parallel, respecting dependencies."""

    async def _run() -> None:
        state_manager = StateManager(workspace)
        try:
            typer.echo("Loading tasks and building execution plan...")
            coordinator = ExecutionCoordinator(state_manager)
            report = await coordinator.execute_all()

            # Header
            status_color = {
                ExecutionRunStatus.SUCCESS: typer.colors.GREEN,
                ExecutionRunStatus.PARTIAL: typer.colors.YELLOW,
                ExecutionRunStatus.FAILED: typer.colors.RED,
                ExecutionRunStatus.EMPTY: typer.colors.WHITE,
            }.get(report.status, typer.colors.WHITE)

            typer.secho(
                f"\nExecution Complete — Run #{report.run_id}",
                fg=typer.colors.GREEN,
                bold=True,
            )
            typer.echo("-" * 48)
            typer.echo(f"Tasks Executed:      {report.total_tasks}")
            typer.echo(f"  Completed:         {report.completed_tasks}")
            if report.failed_tasks:
                typer.secho(
                    f"  Failed:            {report.failed_tasks}", fg=typer.colors.RED
                )
            if report.skipped_tasks:
                typer.secho(
                    f"  Skipped:           {report.skipped_tasks}",
                    fg=typer.colors.YELLOW,
                )
            typer.echo(f"Batches:             {report.total_batches}")
            typer.echo(f"Artifacts Generated: {report.artifacts_generated}")
            typer.echo(
                f"Duration:            {report.duration_seconds:.2f}s"
            )
            if report.workers_used:
                typer.echo(f"Workers Used:        {', '.join(report.workers_used)}")
            typer.echo(f"Completion Rate:     {report.completion_rate}%")
            typer.secho(
                f"\nStatus: {report.status.upper()}", fg=status_color, bold=True
            )

            # Per-task results
            if report.task_results:
                typer.echo("\nTask Results:")
                for res in report.task_results:
                    icon = {
                        TaskExecutionStatus.COMPLETED: "✓",
                        TaskExecutionStatus.FAILED: "✗",
                        TaskExecutionStatus.SKIPPED: "⊘",
                    }.get(res.status, "?")
                    color = {
                        TaskExecutionStatus.COMPLETED: typer.colors.GREEN,
                        TaskExecutionStatus.FAILED: typer.colors.RED,
                        TaskExecutionStatus.SKIPPED: typer.colors.YELLOW,
                    }.get(res.status, typer.colors.WHITE)
                    typer.secho(
                        f"  {icon} [{res.assigned_agent:8s}] {res.task_id}: {res.task_title}",
                        fg=color,
                    )
                    if res.error:
                        typer.secho(
                            f"      Error: {res.error}", fg=typer.colors.RED
                        )

            typer.echo("\nOutputs saved to .project/execution/")

        except CyclicDependencyError as exc:
            typer.secho(
                f"Cyclic dependency detected: {exc}", fg=typer.colors.RED, err=True
            )
            raise typer.Exit(1) from exc
        except ExecutionPlanError as exc:
            typer.secho(
                f"Invalid execution plan: {exc}", fg=typer.colors.RED, err=True
            )
            raise typer.Exit(1) from exc
        except OmnixError as exc:
            typer.secho(str(exc), fg=typer.colors.RED, err=True)
            raise typer.Exit(1) from exc
        except Exception as exc:
            typer.secho(f"Unexpected error: {exc}", fg=typer.colors.RED, err=True)
            raise typer.Exit(1) from exc

    asyncio.run(_run())


def execution_command(
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
    """Display execution status, latest run, and history summary."""

    state_manager = StateManager(workspace)
    try:
        report = state_manager.load_execution_report()

        typer.secho(f"Execution Status: {report.project_name}", bold=True)
        typer.echo("-" * 48)
        typer.echo(f"Latest Run ID:       {report.run_id}")
        typer.echo(
            f"Timestamp:           {report.started_at.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        typer.echo(f"Strategy:            {report.strategy}")
        typer.echo(f"Total Batches:       {report.total_batches}")
        typer.echo(f"Tasks Executed:      {report.total_tasks}")
        typer.echo(f"  Completed:         {report.completed_tasks}")
        typer.echo(f"  Failed:            {report.failed_tasks}")
        typer.echo(f"  Skipped:           {report.skipped_tasks}")
        typer.echo(f"Completion Rate:     {report.completion_rate}%")
        typer.echo(f"Artifacts Generated: {report.artifacts_generated}")
        typer.echo(f"Duration:            {report.duration_seconds:.2f}s")

        status_color = typer.colors.GREEN
        if report.status == ExecutionRunStatus.FAILED:
            status_color = typer.colors.RED
        elif report.status == ExecutionRunStatus.PARTIAL:
            status_color = typer.colors.YELLOW
        typer.secho(
            f"\nStatus: {report.status.upper()}", fg=status_color, bold=True
        )

        # History summary
        try:
            history = state_manager.load_execution_history()
            typer.echo(f"\nExecution History: {len(history.runs)} total run(s)")
            for entry in history.runs[-5:]:  # show last 5
                ts = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                typer.echo(
                    f"  {entry.run_id}  {ts}  "
                    f"{entry.completed_tasks}/{entry.total_tasks} completed  "
                    f"{entry.status}"
                )
        except OmnixError:
            pass

    except OmnixError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc
