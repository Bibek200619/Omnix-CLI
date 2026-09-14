"""`omnix build`, `omnix build-status`, and `omnix builds` commands."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Annotated

import typer

from omnix_cli.core.exceptions import OmnixError
from omnix_cli.core.state_manager import StateManager
from omnix_cli.orchestrator import AutonomousOrchestrator
from omnix_cli.schemas.build import BuildConfig, BuildHistory, BuildOutcome, BuildReport


def build_command(
    goal: Annotated[str, typer.Argument(help="Autonomous project goal.")],
    quality_threshold: Annotated[
        int,
        typer.Option(
            "--quality-threshold",
            min=0,
            max=100,
            help="Minimum QA score required to finalize successfully.",
        ),
    ] = 90,
    max_repair_cycles: Annotated[
        int,
        typer.Option(
            "--max-repair-cycles",
            min=0,
            help="Maximum number of autonomous repair cycles.",
        ),
    ] = 3,
    output_json: Annotated[
        bool,
        typer.Option("--json", help="Print the build report as JSON."),
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
    """Run the complete autonomous build lifecycle."""

    state_manager = StateManager(workspace)
    orchestrator = AutonomousOrchestrator(
        state_manager,
        config=BuildConfig(
            quality_threshold=quality_threshold,
            max_repair_cycles=max_repair_cycles,
        ),
        progress_callback=None if output_json else _echo_progress,
    )

    try:
        report = asyncio.run(orchestrator.build(goal))
    except (OmnixError, ValueError) as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc

    if output_json:
        typer.echo(json.dumps(report.model_dump(mode="json"), indent=2))
    else:
        typer.echo(_format_build_report(report, state_manager))

    if report.outcome != BuildOutcome.SUCCESS:
        raise typer.Exit(1)


def build_status_command(
    output_json: Annotated[
        bool,
        typer.Option("--json", help="Print the latest build report as JSON."),
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
    """Display current and latest autonomous build status."""

    state_manager = StateManager(workspace)
    try:
        report = state_manager.load_build_report()
    except OmnixError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc

    if output_json:
        typer.echo(json.dumps(report.model_dump(mode="json"), indent=2))
        return

    current = (
        report.run_id
        if report.status.value in {"pending", "running", "repairing"}
        else "None"
    )
    typer.secho("Build Status", bold=True)
    typer.echo("-" * 48)
    typer.echo(f"Current Build:      {current}")
    typer.echo(f"Last Build:         {report.run_id}")
    typer.echo(f"Goal:               {report.goal}")
    typer.echo(f"Quality Score:      {_score_text(report.final_quality_score)}")
    typer.echo(f"Repair Cycles:      {report.repair_cycles}")
    typer.echo(f"Completion Status:  {report.status}")
    typer.echo(f"Outcome:            {report.outcome}")
    typer.echo(f"Build Duration:     {_duration_text(report.duration_seconds)}")
    if report.completion_reason is not None:
        typer.echo(f"Stop Reason:        {report.completion_reason}")


def builds_command(
    output_json: Annotated[
        bool,
        typer.Option("--json", help="Print build history as JSON."),
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
    """Display autonomous build history and quality trends."""

    state_manager = StateManager(workspace)
    try:
        history = state_manager.load_build_history()
    except OmnixError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc

    if output_json:
        typer.echo(json.dumps(history.model_dump(mode="json"), indent=2))
        return

    typer.secho("Build History", bold=True)
    typer.echo("-" * 72)
    typer.echo(f"Total Builds:       {len(history.runs)}")
    typer.echo(f"Successful Builds:  {_successful_builds(history)}")
    typer.echo(f"Average Quality:    {_average_quality_text(history)}")
    typer.echo(f"Quality Trend:      {_quality_trend(history)}")

    if not history.runs:
        typer.echo("\nNo build runs recorded yet.")
        return

    typer.echo("\nPrevious Runs:")
    typer.echo(
        f"  {'Run ID':12} {'Status':10} {'Outcome':10} {'Score':>5} "
        f"{'Repairs':>7} {'Duration':>10}  Goal"
    )
    for run in history.runs[-10:]:
        typer.echo(
            f"  {run.run_id:12} {run.status:10} {run.outcome:10} "
            f"{_score_text(run.quality_score):>5} {run.repair_cycles:>7} "
            f"{_duration_text(run.duration_seconds):>10}  {run.goal}"
        )


def _echo_progress(message: str) -> None:
    typer.echo(f"[build] {message}")


def _format_build_report(report: BuildReport, state_manager: StateManager) -> str:
    lines = [
        "",
        "Autonomous Build Summary",
        "-" * 48,
        f"Run ID:             {report.run_id}",
        f"Goal:               {report.goal}",
        f"Status:             {report.status}",
        f"Outcome:            {report.outcome}",
        f"Quality Score:      {_score_text(report.final_quality_score)}",
        f"Quality Threshold:  {report.quality_threshold}",
        f"Repair Cycles:      {report.repair_cycles}/{report.max_repair_cycles}",
        f"Tasks:              {report.task_count}",
        f"Artifacts:          {report.artifacts_generated}",
        f"Duration:           {_duration_text(report.duration_seconds)}",
    ]
    if report.completion_reason is not None:
        lines.append(f"Stop Reason:        {report.completion_reason}")
    if report.failures:
        lines.append(f"Failures:           {len(report.failures)}")
        lines.append(f"Latest Failure:     {report.failures[-1].message}")
    lines.extend(
        [
            "",
            f"Build Report:       {state_manager.build_report_path}",
            f"Build History:      {state_manager.build_history_path}",
            f"Final Package:      {state_manager.final_project_package_path}",
        ]
    )
    return "\n".join(lines)


def _score_text(score: int | None) -> str:
    return "n/a" if score is None else str(score)


def _duration_text(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.2f}s"
    minutes = int(seconds // 60)
    remaining = int(seconds % 60)
    return f"{minutes}m {remaining}s"


def _successful_builds(history: BuildHistory) -> int:
    return sum(1 for run in history.runs if run.outcome == BuildOutcome.SUCCESS)


def _average_quality_text(history: BuildHistory) -> str:
    scores = [run.quality_score for run in history.runs if run.quality_score is not None]
    if not scores:
        return "n/a"
    return f"{sum(scores) / len(scores):.1f}"


def _quality_trend(history: BuildHistory) -> str:
    scores = [run.quality_score for run in history.runs if run.quality_score is not None]
    if len(scores) < 2:
        return "insufficient data"
    delta = scores[-1] - scores[0]
    if delta > 0:
        return f"improving (+{delta})"
    if delta < 0:
        return f"declining ({delta})"
    return "stable"
