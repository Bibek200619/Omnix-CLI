"""Autonomous Orchestrator for Phase 10."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from typing import Protocol, TypeVar

from omnix_cli.agents.architect import ArchitectAgent
from omnix_cli.agents.architect.models import ArchitectAgentResult
from omnix_cli.agents.coordinator.coordinator import ExecutionCoordinator
from omnix_cli.agents.coordinator.worker_pool import WorkerPool
from omnix_cli.agents.integration.agent import IntegrationAgent
from omnix_cli.agents.integration.models import IntegrationAgentResult
from omnix_cli.agents.planner import PlannerAgent
from omnix_cli.agents.planner.models import PlannerAgentResult
from omnix_cli.agents.qa.agent import QAAgent
from omnix_cli.agents.qa.models import QAAgentResult
from omnix_cli.agents.repair.agent import RepairAgent
from omnix_cli.agents.repair.models import RepairAgentResult
from omnix_cli.core.exceptions import (
    OmnixError,
    ProjectAlreadyInitializedError,
)
from omnix_cli.core.settings import Settings
from omnix_cli.core.state_manager import StateManager
from omnix_cli.memory.memory_manager import MemoryManager
from omnix_cli.providers.registry import ProviderRegistry
from omnix_cli.schemas.build import (
    BuildBlueprintSummary,
    BuildConfig,
    BuildDecision,
    BuildExecutionStatistics,
    BuildFailure,
    BuildHistory,
    BuildHistoryEntry,
    BuildIntegrationResult,
    BuildMetadata,
    BuildOutcome,
    BuildPhase,
    BuildPhaseResult,
    BuildPhaseStatus,
    BuildQAReports,
    BuildQAResult,
    BuildReport,
    BuildStatus,
    BuildStopReason,
    FinalProjectPackage,
)
from omnix_cli.schemas.execution import ExecutionReport
from omnix_cli.schemas.integration import IntegrationReport
from omnix_cli.schemas.qa import QASummary

OptionalModelT = TypeVar("OptionalModelT")


class BuildPhaseRunner(Protocol):
    """Interface used by the orchestrator to run existing phases."""

    async def run_architect(self) -> ArchitectAgentResult:
        """Generate or refine the architecture blueprint."""

    async def run_planner(self) -> PlannerAgentResult:
        """Generate or refine the task plan."""

    async def run_execution(self) -> ExecutionReport:
        """Execute all tasks."""

    async def run_integration(self) -> IntegrationAgentResult:
        """Integrate generated artifacts."""

    async def run_qa(self) -> QAAgentResult:
        """Evaluate integrated project quality."""

    async def run_repair(self) -> RepairAgentResult:
        """Generate repair artifacts for QA findings."""


class DefaultBuildPhaseRunner:
    """Default phase runner that delegates to the existing Phase 3-9 systems."""

    def __init__(
        self,
        state_manager: StateManager,
        *,
        provider_registry: ProviderRegistry | None = None,
        settings: Settings | None = None,
        worker_pool: WorkerPool | None = None,
    ) -> None:
        self.state_manager = state_manager
        self.provider_registry = provider_registry
        self.settings = settings
        self.worker_pool = worker_pool

    async def run_architect(self) -> ArchitectAgentResult:
        agent = ArchitectAgent(
            self.state_manager,
            provider_registry=self.provider_registry,
            settings=self.settings,
        )
        return await agent.run()

    async def run_planner(self) -> PlannerAgentResult:
        agent = PlannerAgent(
            self.state_manager,
            provider_registry=self.provider_registry,
            settings=self.settings,
        )
        return await agent.run()

    async def run_execution(self) -> ExecutionReport:
        coordinator = ExecutionCoordinator(
            self.state_manager,
            provider_registry=self.provider_registry,
            settings=self.settings,
            worker_pool=self.worker_pool,
        )
        return await coordinator.execute_all()

    async def run_integration(self) -> IntegrationAgentResult:
        agent = IntegrationAgent(
            self.state_manager,
            provider_registry=self.provider_registry,
            settings=self.settings,
        )
        return await agent.integrate()

    async def run_qa(self) -> QAAgentResult:
        agent = QAAgent(
            self.state_manager,
            provider_registry=self.provider_registry,
            settings=self.settings,
        )
        return await agent.evaluate()

    async def run_repair(self) -> RepairAgentResult:
        agent = RepairAgent(
            self.state_manager,
            provider_registry=self.provider_registry,
            settings=self.settings,
        )
        return await agent.repair()


class AutonomousOrchestrator:
    """Coordinates the full autonomous project build lifecycle."""

    def __init__(
        self,
        state_manager: StateManager,
        *,
        config: BuildConfig | None = None,
        phase_runner: BuildPhaseRunner | None = None,
        memory_manager: MemoryManager | None = None,
        progress_callback: Callable[[str], None] | None = None,
    ) -> None:
        self.state_manager = state_manager
        self.config = config or BuildConfig()
        self.phase_runner = phase_runner or DefaultBuildPhaseRunner(state_manager)
        self.memory_manager = memory_manager or MemoryManager(state_manager)
        self.progress_callback = progress_callback
        self._manual_stop_requested = False

    def request_stop(self) -> None:
        """Request a manual stop at the next phase boundary."""

        self._manual_stop_requested = True

    async def build(self, goal: str) -> BuildReport:
        """Run an autonomous build from goal to final package or terminal stop."""

        normalized_goal = goal.strip()
        if not normalized_goal:
            msg = "Build goal cannot be empty."
            raise ValueError(msg)

        self._ensure_project_initialized(normalized_goal)
        self._recover_incomplete_latest_run()

        report = BuildReport(
            run_id=self.state_manager.get_next_build_run_id(),
            goal=normalized_goal,
            status=BuildStatus.PENDING,
            quality_threshold=self.config.quality_threshold,
            max_repair_cycles=self.config.max_repair_cycles,
        )
        self._persist_report(report)

        try:
            report.status = BuildStatus.RUNNING
            self._persist_report(report)
            self._emit(f"Build {report.run_id} started")

            self._run_create_goal_phase(report, normalized_goal)
            await self._run_architect_phase(report)
            await self._run_planner_phase(report)

            while True:
                if self._stop_if_requested(report):
                    break

                await self._run_execution_phase(report)
                await self._run_integration_phase(report)
                await self._run_qa_phase(report)

                if self._evaluate_quality(report):
                    break

                if self._stop_if_requested(report):
                    break

                report.status = BuildStatus.REPAIRING
                self._persist_report(report)
                await self._run_repair_phase(report)
                report.repair_cycles += 1
                report.status = BuildStatus.RUNNING
                self._record_decision(
                    report,
                    BuildPhase.REPAIR,
                    "re_execute_after_repair",
                    "Repair artifacts generated; rerunning execution, integration, and QA.",
                    {"repair_cycles": report.repair_cycles},
                )
                self._persist_report(report)

            self._finalize_project_package(report)
            self._persist_report(report)
            self._emit(f"Build {report.run_id} finished with {report.outcome}")
            return report

        except Exception as exc:
            self._record_failure_if_missing(report, BuildPhase.FINALIZE, exc)
            self._record_decision(
                report,
                BuildPhase.FINALIZE,
                "abort_build",
                "A phase failed; preserving partial build state and stopping.",
                {"error_type": type(exc).__name__},
            )
            self._complete_report(
                report,
                status=BuildStatus.FAILED,
                outcome=BuildOutcome.FAILED,
                reason=BuildStopReason.FATAL_FAILURE,
            )
            try:
                self._finalize_project_package(report)
            except Exception as finalize_exc:
                self._record_failure(report, BuildPhase.FINALIZE, finalize_exc)
            self._persist_report(report)
            self._emit(f"Build {report.run_id} failed: {exc}")
            return report

    def _run_create_goal_phase(self, report: BuildReport, goal: str) -> None:
        phase = self._start_phase(report, BuildPhase.CREATE_GOAL)
        try:
            project_goal = self.memory_manager.add_goal(goal)
        except Exception as exc:
            self._fail_phase(report, phase, exc)
            raise
        self._finish_phase(
            report,
            phase,
            summary=f"Goal recorded as {project_goal.id}.",
            metadata={"goal_id": project_goal.id},
        )

    async def _run_architect_phase(self, report: BuildReport) -> None:
        phase = self._start_phase(report, BuildPhase.ARCHITECT)
        try:
            result = await self.phase_runner.run_architect()
        except Exception as exc:
            self._fail_phase(report, phase, exc)
            raise
        self._finish_phase(
            report,
            phase,
            summary="Blueprint generated.",
            metadata={
                "provider": result.provider,
                "model": result.model,
                "features": result.feature_count,
                "entities": result.entity_count,
                "modules": result.module_count,
            },
        )
        self._refresh_state_metrics(report)

    async def _run_planner_phase(self, report: BuildReport) -> None:
        phase = self._start_phase(report, BuildPhase.PLAN)
        try:
            result = await self.phase_runner.run_planner()
        except Exception as exc:
            self._fail_phase(report, phase, exc)
            raise
        self._finish_phase(
            report,
            phase,
            summary="Task plan generated.",
            metadata={
                "provider": result.provider,
                "model": result.model,
                "task_count": result.task_count,
                "new_task_count": result.new_task_count,
                "updated_task_count": result.updated_task_count,
            },
        )
        report.task_count = result.task_count
        self._refresh_state_metrics(report)

    async def _run_execution_phase(self, report: BuildReport) -> None:
        phase = self._start_phase(report, BuildPhase.EXECUTE)
        try:
            result = await self.phase_runner.run_execution()
        except Exception as exc:
            self._fail_phase(report, phase, exc)
            raise
        self._add_execution_statistics(report, result)
        self._finish_phase(
            report,
            phase,
            summary=f"Execution run {result.run_id} finished with {result.status}.",
            metadata={
                "run_id": result.run_id,
                "status": result.status,
                "total_tasks": result.total_tasks,
                "completed_tasks": result.completed_tasks,
                "failed_tasks": result.failed_tasks,
                "skipped_tasks": result.skipped_tasks,
                "artifacts_generated": result.artifacts_generated,
            },
        )
        self._refresh_state_metrics(report)

    async def _run_integration_phase(self, report: BuildReport) -> None:
        phase = self._start_phase(report, BuildPhase.INTEGRATE)
        try:
            result = await self.phase_runner.run_integration()
        except Exception as exc:
            self._fail_phase(report, phase, exc)
            raise
        self._set_integration_result(report, result.integration_report)
        self._finish_phase(
            report,
            phase,
            summary="Artifacts integrated.",
            metadata={
                "status": result.integration_report.status,
                "artifacts_processed": result.integration_report.artifacts_processed,
                "dependencies_found": result.integration_report.dependencies_found,
                "conflicts_found": result.integration_report.conflicts_found,
            },
        )
        self._refresh_state_metrics(report)

    async def _run_qa_phase(self, report: BuildReport) -> None:
        phase = self._start_phase(report, BuildPhase.QA)
        try:
            result = await self.phase_runner.run_qa()
        except Exception as exc:
            self._fail_phase(report, phase, exc)
            raise
        self._set_qa_result(report, result.summary)
        self._finish_phase(
            report,
            phase,
            summary=f"QA completed with score {result.summary.quality_score}.",
            metadata={
                "version": result.summary.version,
                "quality_score": result.summary.quality_score,
                "coverage_score": result.summary.coverage_score,
                "status": result.summary.status,
            },
        )
        self._refresh_state_metrics(report)

    async def _run_repair_phase(self, report: BuildReport) -> None:
        phase = self._start_phase(report, BuildPhase.REPAIR)
        try:
            result = await self.phase_runner.run_repair()
        except Exception as exc:
            self._fail_phase(report, phase, exc)
            raise
        self._finish_phase(
            report,
            phase,
            summary=f"Repair cycle {result.cycle} generated.",
            metadata={
                "cycle": result.cycle,
                "issues_processed": result.repair_report.issues_processed,
                "artifacts_generated": result.repair_report.artifacts_generated,
            },
        )
        self._refresh_state_metrics(report)

    def _evaluate_quality(self, report: BuildReport) -> bool:
        phase = self._start_phase(report, BuildPhase.QUALITY_CHECK)
        score = report.final_quality_score
        if score is None:
            msg = "QA phase did not produce a final quality score."
            error = RuntimeError(msg)
            self._fail_phase(report, phase, error)
            raise error

        if score >= report.quality_threshold:
            self._record_decision(
                report,
                BuildPhase.QUALITY_CHECK,
                "finalize_build",
                "Quality threshold reached.",
                {"quality_score": score, "quality_threshold": report.quality_threshold},
            )
            self._finish_phase(
                report,
                phase,
                summary="Quality threshold reached.",
                metadata={"quality_score": score},
            )
            self._complete_report(
                report,
                status=BuildStatus.COMPLETED,
                outcome=BuildOutcome.SUCCESS,
                reason=BuildStopReason.QUALITY_THRESHOLD_REACHED,
            )
            return True

        if report.repair_cycles >= report.max_repair_cycles:
            self._record_decision(
                report,
                BuildPhase.QUALITY_CHECK,
                "stop_repair_loop",
                "Maximum repair cycles reached before quality threshold.",
                {
                    "quality_score": score,
                    "quality_threshold": report.quality_threshold,
                    "repair_cycles": report.repair_cycles,
                    "max_repair_cycles": report.max_repair_cycles,
                },
            )
            self._finish_phase(
                report,
                phase,
                summary="Maximum repair cycles reached.",
                metadata={"quality_score": score},
            )
            self._complete_report(
                report,
                status=BuildStatus.FAILED,
                outcome=BuildOutcome.FAILED,
                reason=BuildStopReason.MAX_REPAIR_CYCLES_REACHED,
            )
            return True

        self._record_decision(
            report,
            BuildPhase.QUALITY_CHECK,
            "run_repair",
            "Quality score is below threshold and repair capacity remains.",
            {
                "quality_score": score,
                "quality_threshold": report.quality_threshold,
                "next_repair_cycle": report.repair_cycles + 1,
            },
        )
        self._finish_phase(
            report,
            phase,
            summary="Repair cycle required.",
            metadata={"quality_score": score},
        )
        return False

    def _stop_if_requested(self, report: BuildReport) -> bool:
        if not self._manual_stop_requested:
            return False

        self._record_decision(
            report,
            BuildPhase.QUALITY_CHECK,
            "manual_stop",
            "Manual stop requested.",
        )
        self._complete_report(
            report,
            status=BuildStatus.CANCELLED,
            outcome=BuildOutcome.CANCELLED,
            reason=BuildStopReason.MANUAL_STOP,
        )
        return True

    def _start_phase(self, report: BuildReport, phase: BuildPhase) -> BuildPhaseResult:
        result = BuildPhaseResult(phase=phase, status=BuildPhaseStatus.RUNNING)
        report.phase_results.append(result)
        self._emit(f"{phase.value} started")
        self._persist_report(report)
        return result

    def _finish_phase(
        self,
        report: BuildReport,
        phase: BuildPhaseResult,
        *,
        summary: str,
        metadata: dict[str, object] | None = None,
    ) -> None:
        finished_at = datetime.now()
        phase.status = BuildPhaseStatus.SUCCESS
        phase.finished_at = finished_at
        phase.duration_seconds = (finished_at - phase.started_at).total_seconds()
        phase.summary = summary
        phase.metadata = metadata or {}
        self._emit(f"{phase.phase.value} completed")
        self._persist_report(report)

    def _fail_phase(
        self,
        report: BuildReport,
        phase: BuildPhaseResult,
        exc: Exception,
    ) -> None:
        finished_at = datetime.now()
        phase.status = BuildPhaseStatus.FAILED
        phase.finished_at = finished_at
        phase.duration_seconds = (finished_at - phase.started_at).total_seconds()
        phase.error = str(exc)
        self._record_failure(report, phase.phase, exc)
        self._persist_report(report)

    def _record_failure(
        self,
        report: BuildReport,
        phase: BuildPhase,
        exc: Exception,
    ) -> None:
        report.failures.append(
            BuildFailure(
                phase=phase,
                error_type=type(exc).__name__,
                message=str(exc),
            )
        )

    def _record_failure_if_missing(
        self,
        report: BuildReport,
        phase: BuildPhase,
        exc: Exception,
    ) -> None:
        if report.failures:
            return
        self._record_failure(report, phase, exc)

    def _record_decision(
        self,
        report: BuildReport,
        phase: BuildPhase,
        decision: str,
        rationale: str,
        data: dict[str, object] | None = None,
    ) -> None:
        report.decisions.append(
            BuildDecision(
                phase=phase,
                decision=decision,
                rationale=rationale,
                data=data or {},
            )
        )

    def _complete_report(
        self,
        report: BuildReport,
        *,
        status: BuildStatus,
        outcome: BuildOutcome,
        reason: BuildStopReason,
    ) -> None:
        finished_at = datetime.now()
        report.status = status
        report.outcome = outcome
        report.completion_reason = reason
        report.finished_at = finished_at
        report.duration_seconds = (finished_at - report.started_at).total_seconds()
        self._refresh_state_metrics(report)
        self._persist_report(report)

    def _refresh_state_metrics(self, report: BuildReport) -> None:
        with suppress(OmnixError):
            blueprint = self.state_manager.load_blueprint()
            report.blueprint_summary = BuildBlueprintSummary(
                project_name=blueprint.project_name,
                description=blueprint.description,
                feature_count=len(blueprint.features),
                entity_count=len(blueprint.entities),
                module_count=len(blueprint.modules),
                page_count=len(blueprint.pages),
                api_count=len(blueprint.apis),
                architecture_note_count=len(blueprint.architecture_notes),
            )

        with suppress(OmnixError):
            report.task_count = len(self.state_manager.load_tasks().tasks)

        report.artifacts_generated = len(self.state_manager.list_artifacts())

    def _add_execution_statistics(
        self,
        report: BuildReport,
        execution_report: ExecutionReport,
    ) -> None:
        stats = report.execution_statistics
        report.execution_statistics = BuildExecutionStatistics(
            total_runs=stats.total_runs + 1,
            latest_run_id=execution_report.run_id,
            total_tasks_executed=(
                stats.total_tasks_executed + execution_report.total_tasks
            ),
            total_completed_tasks=(
                stats.total_completed_tasks + execution_report.completed_tasks
            ),
            total_failed_tasks=(
                stats.total_failed_tasks + execution_report.failed_tasks
            ),
            total_skipped_tasks=(
                stats.total_skipped_tasks + execution_report.skipped_tasks
            ),
            artifacts_generated=(
                stats.artifacts_generated + execution_report.artifacts_generated
            ),
            total_duration_seconds=(
                stats.total_duration_seconds + execution_report.duration_seconds
            ),
        )

    def _set_integration_result(
        self,
        report: BuildReport,
        integration_report: IntegrationReport,
    ) -> None:
        report.integration_result = BuildIntegrationResult(
            status=integration_report.status,
            artifacts_processed=integration_report.artifacts_processed,
            dependencies_found=integration_report.dependencies_found,
            conflicts_found=integration_report.conflicts_found,
            coverage_status=integration_report.coverage_status,
            summary=integration_report.summary,
        )

    def _set_qa_result(self, report: BuildReport, summary: QASummary) -> None:
        report.final_quality_score = summary.quality_score
        report.qa_result = BuildQAResult(
            version=summary.version,
            quality_score=summary.quality_score,
            coverage_score=summary.coverage_score,
            gap_score=summary.gap_score,
            risk_score=summary.risk_score,
            critical_issues=summary.critical_issues,
            high_issues=summary.high_issues,
            medium_issues=summary.medium_issues,
            low_issues=summary.low_issues,
            status=summary.status,
        )

    def _finalize_project_package(self, report: BuildReport) -> None:
        phase = self._start_phase(report, BuildPhase.FINALIZE)
        try:
            report_copy = BuildReport.model_validate(report)
            package = FinalProjectPackage(
                build_metadata=BuildMetadata(
                    run_id=report.run_id,
                    goal=report.goal,
                    status=report.status,
                    outcome=report.outcome,
                    quality_threshold=report.quality_threshold,
                    max_repair_cycles=report.max_repair_cycles,
                    repair_cycles=report.repair_cycles,
                    final_quality_score=report.final_quality_score,
                    completion_reason=report.completion_reason,
                    started_at=report.started_at,
                    finished_at=report.finished_at,
                    duration_seconds=report.duration_seconds,
                ),
                blueprint=self.state_manager.load_blueprint(),
                tasks=self.state_manager.load_tasks(),
                artifacts=self.state_manager.list_artifacts(),
                integrated_package=self._load_optional(
                    self.state_manager.load_integrated_package
                ),
                qa_reports=self._load_qa_reports_optional(),
                repair_history=self._load_optional(self.state_manager.load_repair_history),
                execution_history=self._load_optional(
                    self.state_manager.load_execution_history
                ),
                build_report=report_copy,
            )
            self.state_manager.save_final_project_package(package)
        except Exception as exc:
            self._fail_phase(report, phase, exc)
            raise
        self._finish_phase(
            report,
            phase,
            summary="Final project package generated.",
            metadata={"package_path": str(self.state_manager.final_project_package_path)},
        )

    def _load_qa_reports_optional(self) -> BuildQAReports | None:
        try:
            return BuildQAReports(
                summary=self.state_manager.load_qa_summary(),
                quality=self.state_manager.load_quality_report(),
                coverage=self.state_manager.load_coverage_report(),
                gap=self.state_manager.load_gap_report(),
                risk=self.state_manager.load_risk_report(),
            )
        except OmnixError:
            return None

    def _load_optional(
        self,
        loader: Callable[[], OptionalModelT],
    ) -> OptionalModelT | None:
        try:
            return loader()
        except OmnixError:
            return None

    def _persist_report(self, report: BuildReport) -> None:
        self.state_manager.save_build_report(report)
        self._upsert_history(report)

    def _upsert_history(self, report: BuildReport) -> None:
        try:
            history = self.state_manager.load_build_history()
        except OmnixError:
            history = BuildHistory()

        entry = BuildHistoryEntry(
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

        for index, existing in enumerate(history.runs):
            if existing.run_id == report.run_id:
                history.runs[index] = entry
                break
        else:
            history.runs.append(entry)

        self.state_manager.save_build_history(history)

    def _recover_incomplete_latest_run(self) -> None:
        try:
            latest = self.state_manager.load_build_report()
        except OmnixError:
            return

        if latest.status not in {
            BuildStatus.PENDING,
            BuildStatus.RUNNING,
            BuildStatus.REPAIRING,
        }:
            return

        phase = self._start_phase(latest, BuildPhase.RECOVERY)
        error = RuntimeError("Recovered interrupted autonomous build run.")
        self._record_failure(latest, BuildPhase.RECOVERY, error)
        self._record_decision(
            latest,
            BuildPhase.RECOVERY,
            "mark_interrupted_run_failed",
            "Previous build was not in a terminal state when a new build started.",
        )
        self._finish_phase(
            latest,
            phase,
            summary="Interrupted build marked failed.",
        )
        self._complete_report(
            latest,
            status=BuildStatus.FAILED,
            outcome=BuildOutcome.FAILED,
            reason=BuildStopReason.FATAL_FAILURE,
        )

    def _ensure_project_initialized(self, goal: str) -> None:
        required_paths = [
            self.state_manager.blueprint_path,
            self.state_manager.memory_path,
            self.state_manager.models_path,
            self.state_manager.tasks_path,
        ]
        if all(path.exists() for path in required_paths):
            return

        if any(path.exists() for path in required_paths):
            return

        try:
            self.state_manager.init_project(
                project_name=self._derive_project_name(goal),
                description=goal,
            )
        except ProjectAlreadyInitializedError:
            return

    def _derive_project_name(self, goal: str) -> str:
        normalized = " ".join(goal.split())
        prefix = "Build "
        if normalized.casefold().startswith(prefix.casefold()):
            normalized = normalized[len(prefix) :].strip()
        return normalized[:80] or "Omnix Build"

    def _emit(self, message: str) -> None:
        if self.progress_callback is not None:
            self.progress_callback(message)


def build_state_manager(workspace: Path) -> StateManager:
    """Small factory used by callers that need a StateManager for a workspace."""

    return StateManager(workspace)
