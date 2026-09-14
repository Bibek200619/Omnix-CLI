"""Tests for Phase 10: Autonomous Orchestrator."""

from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path

import pytest
from typer.testing import CliRunner

from omnix_cli.agents.architect.models import ArchitectAgentResult
from omnix_cli.agents.integration.models import IntegrationAgentResult
from omnix_cli.agents.planner.models import PlannerAgentResult
from omnix_cli.agents.qa.models import QAAgentResult
from omnix_cli.agents.repair.models import RepairAgentResult
from omnix_cli.cli.main import app
from omnix_cli.core.state_manager import StateManager
from omnix_cli.orchestrator import AutonomousOrchestrator
from omnix_cli.schemas.artifacts import Artifact, ArtifactType
from omnix_cli.schemas.blueprint import (
    ArchitectureNote,
    EntityDefinition,
    FeatureDefinition,
    ModuleDefinition,
    PageDefinition,
    ProjectBlueprint,
)
from omnix_cli.schemas.build import (
    BuildConfig,
    BuildHistory,
    BuildHistoryEntry,
    BuildOutcome,
    BuildPhase,
    BuildReport,
    BuildStatus,
    BuildStopReason,
)
from omnix_cli.schemas.execution import (
    ExecutionHistory,
    ExecutionHistoryEntry,
    ExecutionReport,
    ExecutionRunStatus,
    ExecutionStrategy,
)
from omnix_cli.schemas.integration import (
    ConflictReport,
    DependencyGraph,
    IntegratedPackage,
    IntegrationReport,
    IntegrationStatus,
)
from omnix_cli.schemas.qa import (
    CoverageReport,
    GapReport,
    QAStatus,
    QASummary,
    QualityReport,
    RiskReport,
)
from omnix_cli.schemas.repair import (
    RepairCycleEntry,
    RepairHistory,
    RepairPlan,
    RepairReport,
)
from omnix_cli.schemas.tasks import (
    TaskAssignedAgent,
    TaskDefinition,
    TaskPlan,
    TaskPriority,
    TaskStatus,
)


class FakePhaseRunner:
    """Deterministic phase runner that mimics persisted outputs from each phase."""

    def __init__(
        self,
        state_manager: StateManager,
        *,
        qa_scores: list[int],
        fail_phase: BuildPhase | None = None,
    ) -> None:
        self.state_manager = state_manager
        self.qa_scores = qa_scores
        self.fail_phase = fail_phase
        self.calls: list[str] = []
        self.execution_calls = 0
        self.qa_calls = 0
        self.repair_calls = 0

    async def run_architect(self) -> ArchitectAgentResult:
        self._fail_if(BuildPhase.ARCHITECT)
        self.calls.append("architect")
        blueprint = _blueprint()
        self.state_manager.save_blueprint(blueprint)
        return ArchitectAgentResult(
            provider="fake",
            model="architect",
            blueprint=blueprint,
            feature_count=len(blueprint.features),
            entity_count=len(blueprint.entities),
            module_count=len(blueprint.modules),
            architecture_note_count=len(blueprint.architecture_notes),
        )

    async def run_planner(self) -> PlannerAgentResult:
        self._fail_if(BuildPhase.PLAN)
        self.calls.append("planner")
        task_plan = _task_plan()
        self.state_manager.save_tasks(task_plan)
        return PlannerAgentResult(
            provider="fake",
            model="planner",
            task_plan=task_plan,
            task_count=len(task_plan.tasks),
            new_task_count=len(task_plan.tasks),
            updated_task_count=0,
            tasks_by_agent={"backend": len(task_plan.tasks)},
        )

    async def run_execution(self) -> ExecutionReport:
        self._fail_if(BuildPhase.EXECUTE)
        self.calls.append("execute")
        self.execution_calls += 1

        task_count = len(self.state_manager.load_tasks().tasks)
        artifact = Artifact(
            id=f"artifact_{self.execution_calls:03d}",
            task_id="task_001",
            agent="backend",
            title=f"Execution Artifact {self.execution_calls}",
            artifact_type=ArtifactType.BACKEND_SERVICE,
            content="generated content",
        )
        self.state_manager.save_artifact(artifact)

        started_at = datetime.now()
        report = ExecutionReport(
            project_name="CRM",
            run_id=f"exec_{self.execution_calls:03d}",
            started_at=started_at,
            finished_at=started_at,
            duration_seconds=0.1,
            strategy=ExecutionStrategy.PARALLEL,
            total_tasks=task_count,
            completed_tasks=task_count,
            failed_tasks=0,
            skipped_tasks=0,
            total_batches=1,
            artifacts_generated=1,
            workers_used=["backend"],
            status=ExecutionRunStatus.SUCCESS,
        )
        self.state_manager.save_execution_report(report)
        self._append_execution_history(report)
        return report

    async def run_integration(self) -> IntegrationAgentResult:
        self._fail_if(BuildPhase.INTEGRATE)
        self.calls.append("integrate")
        artifacts = self.state_manager.list_artifacts()
        package = IntegratedPackage(
            project_name="CRM",
            artifacts=artifacts,
            status=IntegrationStatus.SUCCESS,
        )
        graph = DependencyGraph()
        integration_report = IntegrationReport(
            project_name="CRM",
            status=IntegrationStatus.SUCCESS,
            artifacts_processed=len(artifacts),
            artifacts_by_agent={"backend": len(artifacts)} if artifacts else {},
            dependencies_found=0,
            conflicts_found=0,
            coverage_status="COMPLETE",
            summary="Integrated.",
        )
        conflict_report = ConflictReport(
            project_name="CRM",
            total_conflicts=0,
            conflicts=[],
        )
        self.state_manager.save_integrated_package(package)
        self.state_manager.save_dependency_graph(graph)
        self.state_manager.save_integration_report(integration_report)
        self.state_manager.save_conflict_report(conflict_report)
        return IntegrationAgentResult(
            provider="fake",
            model="integration",
            package=package,
            dependency_graph=graph,
            integration_report=integration_report,
            conflict_report=conflict_report,
        )

    async def run_qa(self) -> QAAgentResult:
        self._fail_if(BuildPhase.QA)
        self.calls.append("qa")
        score_index = min(self.qa_calls, len(self.qa_scores) - 1)
        score = self.qa_scores[score_index]
        self.qa_calls += 1

        status = QAStatus.PASSED if score >= 90 else QAStatus.REVIEW_REQUIRED
        summary = QASummary(
            project_name="CRM",
            version=self.state_manager.get_next_qa_version(),
            quality_score=score,
            coverage_score=score,
            gap_score=score,
            risk_score=score,
            critical_issues=0,
            high_issues=0 if score >= 90 else 1,
            medium_issues=0,
            low_issues=0,
            status=status,
        )
        quality = QualityReport(
            project_name="CRM",
            version=summary.version,
            overall_score=score,
            high_issues=summary.high_issues,
            status=status,
            summary="QA complete.",
        )
        coverage = CoverageReport(
            project_name="CRM",
            version=summary.version,
            coverage_score=score,
        )
        gap = GapReport(project_name="CRM", version=summary.version, gap_score=score)
        risk = RiskReport(project_name="CRM", version=summary.version, risk_score=score)
        self.state_manager.save_qa_reports(
            summary=summary,
            quality=quality,
            coverage=coverage,
            gap=gap,
            risk=risk,
        )
        return QAAgentResult(
            provider="fake",
            model="qa",
            summary=summary,
            quality_report=quality,
            coverage_report=coverage,
            gap_report=gap,
            risk_report=risk,
        )

    async def run_repair(self) -> RepairAgentResult:
        self._fail_if(BuildPhase.REPAIR)
        self.calls.append("repair")
        self.repair_calls += 1
        cycle = self.repair_calls
        plan = RepairPlan(project_name="CRM", cycle=cycle)
        report = RepairReport(
            project_name="CRM",
            cycle=cycle,
            issues_processed=1,
            critical_count=0,
            high_count=1,
            medium_count=0,
            low_count=0,
            artifacts_generated=0,
            expected_impact="Raise quality score.",
        )
        self.state_manager.save_repair_plan(plan)
        self.state_manager.save_repair_report(report)
        self._append_repair_history(cycle)
        return RepairAgentResult(
            provider="fake",
            model="repair",
            cycle=cycle,
            repair_plan=plan,
            repair_artifacts=[],
            repair_report=report,
        )

    def _append_execution_history(self, report: ExecutionReport) -> None:
        try:
            history = self.state_manager.load_execution_history()
        except Exception:
            history = ExecutionHistory(project_name="CRM")
        history.runs.append(
            ExecutionHistoryEntry(
                run_id=report.run_id,
                total_tasks=report.total_tasks,
                completed_tasks=report.completed_tasks,
                failed_tasks=report.failed_tasks,
                skipped_tasks=report.skipped_tasks,
                artifacts_generated=report.artifacts_generated,
                duration_seconds=report.duration_seconds,
                status=report.status,
            )
        )
        self.state_manager.save_execution_history(history)

    def _append_repair_history(self, cycle: int) -> None:
        try:
            history = self.state_manager.load_repair_history()
        except Exception:
            history = RepairHistory(project_name="CRM")
        history.cycles.append(
            RepairCycleEntry(
                cycle=cycle,
                issues_addressed=1,
                artifacts_generated=0,
                quality_score_before=80,
                status="COMPLETE",
            )
        )
        self.state_manager.save_repair_history(history)

    def _fail_if(self, phase: BuildPhase) -> None:
        if self.fail_phase == phase:
            msg = f"Injected failure in {phase.value}"
            raise RuntimeError(msg)


def test_full_build_lifecycle_repairs_and_finalizes(tmp_path: Path) -> None:
    sm = _initialized_state(tmp_path)
    runner = FakePhaseRunner(sm, qa_scores=[84, 91])

    report = asyncio.run(
        AutonomousOrchestrator(
            sm,
            config=BuildConfig(quality_threshold=90, max_repair_cycles=3),
            phase_runner=runner,
        ).build("Build a CRM")
    )

    assert report.status == BuildStatus.COMPLETED
    assert report.outcome == BuildOutcome.SUCCESS
    assert report.completion_reason == BuildStopReason.QUALITY_THRESHOLD_REACHED
    assert report.final_quality_score == 91
    assert report.repair_cycles == 1
    assert runner.calls == [
        "architect",
        "planner",
        "execute",
        "integrate",
        "qa",
        "repair",
        "execute",
        "integrate",
        "qa",
    ]

    assert sm.load_build_report().run_id == report.run_id
    assert len(sm.load_build_history().runs) == 1
    package = sm.load_final_project_package()
    assert package.build_metadata.run_id == report.run_id
    assert package.qa_reports is not None
    assert package.execution_history is not None
    assert (sm.build_runs_dir / report.run_id / "build_report.json").exists()
    assert (sm.build_runs_dir / report.run_id / "final_project_package.json").exists()


def test_quality_threshold_stops_without_repair(tmp_path: Path) -> None:
    sm = _initialized_state(tmp_path)
    runner = FakePhaseRunner(sm, qa_scores=[90])

    report = asyncio.run(
        AutonomousOrchestrator(
            sm,
            config=BuildConfig(quality_threshold=90, max_repair_cycles=3),
            phase_runner=runner,
        ).build("Build a CRM")
    )

    assert report.outcome == BuildOutcome.SUCCESS
    assert report.repair_cycles == 0
    assert runner.repair_calls == 0
    assert runner.qa_calls == 1
    assert any(decision.decision == "finalize_build" for decision in report.decisions)


def test_repair_loop_stops_at_max_cycles(tmp_path: Path) -> None:
    sm = _initialized_state(tmp_path)
    runner = FakePhaseRunner(sm, qa_scores=[70, 80, 85])

    report = asyncio.run(
        AutonomousOrchestrator(
            sm,
            config=BuildConfig(quality_threshold=90, max_repair_cycles=2),
            phase_runner=runner,
        ).build("Build a CRM")
    )

    assert report.status == BuildStatus.FAILED
    assert report.outcome == BuildOutcome.FAILED
    assert report.completion_reason == BuildStopReason.MAX_REPAIR_CYCLES_REACHED
    assert report.repair_cycles == 2
    assert runner.repair_calls == 2
    assert runner.execution_calls == 3
    assert runner.qa_calls == 3
    assert sm.load_final_project_package().build_metadata.outcome == BuildOutcome.FAILED


def test_phase_failure_is_recorded_and_history_is_preserved(tmp_path: Path) -> None:
    sm = _initialized_state(tmp_path)
    runner = FakePhaseRunner(sm, qa_scores=[95], fail_phase=BuildPhase.INTEGRATE)

    report = asyncio.run(
        AutonomousOrchestrator(
            sm,
            config=BuildConfig(),
            phase_runner=runner,
        ).build("Build a CRM")
    )

    assert report.status == BuildStatus.FAILED
    assert report.outcome == BuildOutcome.FAILED
    assert report.completion_reason == BuildStopReason.FATAL_FAILURE
    assert report.failures[0].phase == BuildPhase.INTEGRATE
    assert "Injected failure" in report.failures[0].message
    assert sm.load_build_report().status == BuildStatus.FAILED
    assert sm.load_build_history().runs[0].status == BuildStatus.FAILED
    assert sm.load_final_project_package().integrated_package is None


def test_state_recovery_marks_interrupted_run_failed(tmp_path: Path) -> None:
    sm = _initialized_state(tmp_path)
    interrupted = BuildReport(
        run_id="build_0001",
        goal="Old build",
        status=BuildStatus.RUNNING,
        outcome=BuildOutcome.INCOMPLETE,
    )
    sm.save_build_report(interrupted)
    sm.save_build_history(
        BuildHistory(
            runs=[
                BuildHistoryEntry(
                    run_id=interrupted.run_id,
                    goal=interrupted.goal,
                    started_at=interrupted.started_at,
                    status=interrupted.status,
                    outcome=interrupted.outcome,
                )
            ]
        )
    )

    runner = FakePhaseRunner(sm, qa_scores=[95])
    report = asyncio.run(
        AutonomousOrchestrator(sm, phase_runner=runner).build("Build a CRM")
    )

    history = sm.load_build_history()
    assert report.run_id == "build_0002"
    assert len(history.runs) == 2
    assert history.runs[0].run_id == "build_0001"
    assert history.runs[0].status == BuildStatus.FAILED
    assert history.runs[0].completion_reason == BuildStopReason.FATAL_FAILURE
    assert history.runs[1].run_id == "build_0002"
    assert history.runs[1].outcome == BuildOutcome.SUCCESS


def test_build_cli_commands(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from omnix_cli.cli.commands import build as build_module

    class FakeOrchestrator:
        def __init__(
            self,
            state_manager: StateManager,
            *_: object,
            **__: object,
        ) -> None:
            self.state_manager = state_manager

        async def build(self, goal: str) -> BuildReport:
            report = _successful_report("build_0001", goal)
            self.state_manager.save_build_report(report)
            self.state_manager.save_build_history(
                BuildHistory(
                    runs=[
                        BuildHistoryEntry(
                            run_id=report.run_id,
                            goal=report.goal,
                            started_at=report.started_at,
                            finished_at=report.finished_at,
                            duration_seconds=report.duration_seconds,
                            status=report.status,
                            outcome=report.outcome,
                            quality_score=report.final_quality_score,
                            repair_cycles=report.repair_cycles,
                            artifacts_generated=report.artifacts_generated,
                            completion_reason=report.completion_reason,
                        )
                    ]
                )
            )
            return report

    monkeypatch.setattr(build_module, "AutonomousOrchestrator", FakeOrchestrator)

    runner = CliRunner()
    build_result = runner.invoke(app, ["build", "Build a CRM", "-w", str(tmp_path)])
    assert build_result.exit_code == 0, build_result.output
    assert "Autonomous Build Summary" in build_result.output
    assert "Quality Score:      94" in build_result.output

    status_result = runner.invoke(app, ["build-status", "-w", str(tmp_path)])
    assert status_result.exit_code == 0, status_result.output
    assert "Build Status" in status_result.output
    assert "Last Build:         build_0001" in status_result.output

    history_result = runner.invoke(app, ["builds", "-w", str(tmp_path)])
    assert history_result.exit_code == 0, history_result.output
    assert "Build History" in history_result.output
    assert "Successful Builds:  1" in history_result.output


def test_build_status_without_report_fails(tmp_path: Path) -> None:
    _initialized_state(tmp_path)
    runner = CliRunner()

    result = runner.invoke(app, ["build-status", "-w", str(tmp_path)])

    assert result.exit_code == 1
    assert "Build report not found" in result.output


def _initialized_state(tmp_path: Path) -> StateManager:
    sm = StateManager(tmp_path)
    sm.init_project(project_name="CRM")
    return sm


def _blueprint() -> ProjectBlueprint:
    return ProjectBlueprint(
        project_name="CRM",
        description="Customer relationship management workspace.",
        pages=[
            PageDefinition(
                name="Contacts",
                path="/contacts",
                description="Manage contacts.",
            )
        ],
        features=[
            FeatureDefinition(
                name="Contact Management",
                description="Capture customer contacts.",
            )
        ],
        entities=[EntityDefinition(name="Contact")],
        modules=[ModuleDefinition(name="Sales")],
        architecture_notes=[ArchitectureNote(content="CRM architecture.")],
    )


def _task_plan() -> TaskPlan:
    return TaskPlan(
        tasks=[
            TaskDefinition(
                id="task_001",
                title="Create CRM backend",
                assigned_agent=TaskAssignedAgent.BACKEND,
                priority=TaskPriority.HIGH,
                status=TaskStatus.PENDING,
                dependencies=[],
                blueprint_reference="contact_management",
            )
        ]
    )


def _successful_report(run_id: str, goal: str) -> BuildReport:
    started_at = datetime.now()
    report = BuildReport(
        run_id=run_id,
        goal=goal,
        status=BuildStatus.COMPLETED,
        outcome=BuildOutcome.SUCCESS,
        started_at=started_at,
        finished_at=started_at,
        duration_seconds=1.25,
        quality_threshold=90,
        max_repair_cycles=3,
        repair_cycles=1,
        final_quality_score=94,
        completion_reason=BuildStopReason.QUALITY_THRESHOLD_REACHED,
        task_count=3,
        artifacts_generated=4,
    )
    return report
