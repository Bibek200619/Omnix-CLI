"""Execution Coordinator — the runtime brain for Phase 9."""

from __future__ import annotations

import uuid
from datetime import datetime

from omnix_cli.agents.backend.agent import BackendAgent
from omnix_cli.agents.coordinator.dag import (
    build_agent_map,
    build_dependency_map,
    build_execution_batches,
)
from omnix_cli.agents.coordinator.worker_pool import WorkerAgent, WorkerPool
from omnix_cli.agents.database.agent import DatabaseAgent
from omnix_cli.agents.frontend.agent import FrontendAgent
from omnix_cli.agents.routing.agent import RoutingAgent
from omnix_cli.core.settings import Settings
from omnix_cli.core.state_manager import StateManager
from omnix_cli.providers.registry import ProviderRegistry, build_default_provider_registry
from omnix_cli.schemas.execution import (
    ExecutionHistory,
    ExecutionHistoryEntry,
    ExecutionPlan,
    ExecutionReport,
    ExecutionRunStatus,
    ExecutionStrategy,
    TaskExecutionResult,
    TaskExecutionStatus,
)
from omnix_cli.schemas.tasks import TaskDefinition


class ExecutionCoordinator:
    """Orchestrates parallel multi-agent task execution.

    Responsibilities:
    - Read tasks and build a DAG-derived execution plan.
    - Dispatch independent tasks concurrently via the WorkerPool.
    - Track per-task results, skipping dependents of failed tasks.
    - Persist execution plan, report, and history.
    """

    def __init__(
        self,
        state_manager: StateManager,
        *,
        provider_registry: ProviderRegistry | None = None,
        settings: Settings | None = None,
        worker_pool: WorkerPool | None = None,
    ) -> None:
        self.state_manager = state_manager
        self._settings = settings or Settings()
        self._registry = provider_registry or build_default_provider_registry(
            self._settings
        )
        self._worker_pool = worker_pool  # injected in tests; built lazily otherwise

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def execute_all(self) -> ExecutionReport:
        """Build a plan and execute all tasks respecting dependencies."""

        task_plan = self.state_manager.load_tasks()
        tasks = task_plan.tasks

        started_at = datetime.now()
        run_id = str(uuid.uuid4())[:8]

        blueprint = self.state_manager.load_blueprint()
        project_name = blueprint.project_name

        # Handle empty task plan gracefully
        if not tasks:
            report = self._build_empty_report(project_name, run_id, started_at)
            self._persist(
                ExecutionPlan(
                    project_name=project_name,
                    total_tasks=0,
                    batches=[],
                ),
                report,
                project_name,
            )
            return report

        # Build execution plan
        batches = build_execution_batches(tasks)
        dep_map = build_dependency_map(tasks)
        agent_map = build_agent_map(tasks)

        plan = ExecutionPlan(
            project_name=project_name,
            strategy=ExecutionStrategy.PARALLEL,
            total_tasks=len(tasks),
            batches=batches,
            dependency_map=dep_map,
            agent_map=agent_map,
        )
        self.state_manager.save_execution_plan(plan)

        # Build worker pool
        pool = self._worker_pool or self._build_worker_pool()

        # Execute batches sequentially; within each batch tasks run concurrently
        task_index = {t.id: t for t in tasks}
        all_results: list[TaskExecutionResult] = []
        failed_ids: set[str] = set()  # tasks that failed or were skipped

        for batch in batches:
            batch_tasks: list[TaskDefinition] = []
            skipped_results: list[TaskExecutionResult] = []

            for tid in batch.task_ids:
                task = task_index[tid]
                # Skip if any dependency failed
                blocked_by = [d for d in task.dependencies if d in failed_ids]
                if blocked_by:
                    failed_ids.add(tid)
                    skipped_results.append(
                        TaskExecutionResult(
                            task_id=tid,
                            task_title=task.title,
                            assigned_agent=task.assigned_agent.value,
                            status=TaskExecutionStatus.SKIPPED,
                            error=f"Skipped — dependency failed: {blocked_by}",
                        )
                    )
                else:
                    batch_tasks.append(task)

            all_results.extend(skipped_results)

            if batch_tasks:
                batch_results = await pool.run_batch(batch_tasks)
                for res in batch_results:
                    if res.status == TaskExecutionStatus.FAILED:
                        failed_ids.add(res.task_id)
                all_results.extend(batch_results)

        # Build report
        finished_at = datetime.now()
        report = self._build_report(
            project_name, run_id, started_at, finished_at, plan, all_results
        )
        self._persist(plan, report, project_name)
        return report

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_worker_pool(self) -> WorkerPool:
        """Construct the default worker pool from the four worker agents."""
        sm = self.state_manager
        workers: dict[str, WorkerAgent] = {
            "frontend": FrontendAgent(sm, provider_registry=self._registry),
            "backend": BackendAgent(sm, provider_registry=self._registry),
            "database": DatabaseAgent(sm, provider_registry=self._registry),
            "routing": RoutingAgent(sm, provider_registry=self._registry),
        }
        return WorkerPool(workers)

    def _build_report(
        self,
        project_name: str,
        run_id: str,
        started_at: datetime,
        finished_at: datetime,
        plan: ExecutionPlan,
        results: list[TaskExecutionResult],
    ) -> ExecutionReport:
        completed = sum(
            1 for r in results if r.status == TaskExecutionStatus.COMPLETED
        )
        failed = sum(
            1 for r in results if r.status == TaskExecutionStatus.FAILED
        )
        skipped = sum(
            1 for r in results if r.status == TaskExecutionStatus.SKIPPED
        )
        artifacts = sum(1 for r in results if r.artifact_id is not None)
        workers_used = sorted(
            {r.assigned_agent for r in results if r.status == TaskExecutionStatus.COMPLETED}
        )
        duration = (finished_at - started_at).total_seconds()

        if failed == 0 and skipped == 0:
            status = ExecutionRunStatus.SUCCESS
        elif completed == 0:
            status = ExecutionRunStatus.FAILED
        else:
            status = ExecutionRunStatus.PARTIAL

        return ExecutionReport(
            project_name=project_name,
            run_id=run_id,
            started_at=started_at,
            finished_at=finished_at,
            duration_seconds=duration,
            strategy=plan.strategy,
            total_tasks=plan.total_tasks,
            completed_tasks=completed,
            failed_tasks=failed,
            skipped_tasks=skipped,
            total_batches=len(plan.batches),
            artifacts_generated=artifacts,
            workers_used=workers_used,
            task_results=results,
            status=status,
        )

    def _build_empty_report(
        self, project_name: str, run_id: str, started_at: datetime
    ) -> ExecutionReport:
        finished_at = datetime.now()
        return ExecutionReport(
            project_name=project_name,
            run_id=run_id,
            started_at=started_at,
            finished_at=finished_at,
            duration_seconds=(finished_at - started_at).total_seconds(),
            strategy=ExecutionStrategy.PARALLEL,
            total_tasks=0,
            completed_tasks=0,
            failed_tasks=0,
            skipped_tasks=0,
            total_batches=0,
            artifacts_generated=0,
            workers_used=[],
            task_results=[],
            status=ExecutionRunStatus.EMPTY,
        )

    def _persist(
        self,
        plan: ExecutionPlan,
        report: ExecutionReport,
        project_name: str,
    ) -> None:
        """Save plan, report, and append to history."""
        self.state_manager.save_execution_plan(plan)
        self.state_manager.save_execution_report(report)

        # Load or init history
        try:
            history = self.state_manager.load_execution_history()
        except Exception:
            history = ExecutionHistory(project_name=project_name)

        entry = ExecutionHistoryEntry(
            run_id=report.run_id,
            total_tasks=report.total_tasks,
            completed_tasks=report.completed_tasks,
            failed_tasks=report.failed_tasks,
            skipped_tasks=report.skipped_tasks,
            artifacts_generated=report.artifacts_generated,
            duration_seconds=report.duration_seconds,
            status=report.status,
        )
        history.runs.append(entry)
        self.state_manager.save_execution_history(history)
