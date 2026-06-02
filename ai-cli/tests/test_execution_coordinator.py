"""Tests for Phase 9: Parallel Multi-Agent Execution."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from omnix_cli.agents.coordinator.coordinator import ExecutionCoordinator
from omnix_cli.agents.coordinator.dag import (
    build_agent_map,
    build_dependency_map,
    build_execution_batches,
)
from omnix_cli.agents.coordinator.worker_pool import WorkerPool
from omnix_cli.core.exceptions import CyclicDependencyError, ExecutionPlanError
from omnix_cli.core.state_manager import StateManager
from omnix_cli.schemas.artifacts import Artifact, ArtifactType
from omnix_cli.schemas.execution import (
    ExecutionHistory,
    ExecutionRunStatus,
    TaskExecutionStatus,
)
from omnix_cli.schemas.tasks import (
    AgentRole,
    TaskAssignedAgent,
    TaskDefinition,
    TaskPlan,
    TaskPriority,
    TaskStatus,
)


# ---------------------------------------------------------------------------
# Minimal mock worker agent
# ---------------------------------------------------------------------------


class _FakeAgentResult:
    def __init__(self, artifact: Artifact) -> None:
        self.artifact = artifact


class MockWorkerAgent:
    """Synchronous-like worker that returns a canned artifact."""

    def __init__(self, agent_name: str, *, should_fail: bool = False) -> None:
        self._name = agent_name
        self._should_fail = should_fail
        self._call_count = 0

    async def execute_task(self, task: TaskDefinition) -> _FakeAgentResult:
        self._call_count += 1
        if self._should_fail:
            msg = f"Simulated failure in {self._name} for task {task.id}"
            raise RuntimeError(msg)
        artifact = Artifact(
            id=f"art_{task.id}_1",
            task_id=task.id,
            agent=self._name,
            title=f"Artifact for {task.title}",
            artifact_type=ArtifactType.BACKEND_SERVICE,
            content="generated content",
            version=1,
        )
        return _FakeAgentResult(artifact)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _task(
    task_id: str,
    agent: TaskAssignedAgent = TaskAssignedAgent.BACKEND,
    deps: list[str] | None = None,
) -> TaskDefinition:
    return TaskDefinition(
        id=task_id,
        title=f"Task {task_id}",
        assigned_agent=agent,
        blueprint_reference="ref",
        dependencies=deps or [],
        priority=TaskPriority.MEDIUM,
        status=TaskStatus.PENDING,
    )


def _sm(tmp_path: Path) -> StateManager:
    sm = StateManager(tmp_path)
    sm.init_project(project_name="Test Execution Project")
    sm.save_models(
        sm.load_models().with_assignment(
            AgentRole.MASTER, provider="mock", model="m"
        )
    )
    return sm


def _pool(
    agents: list[str] | None = None,
    *,
    fail: set[str] | None = None,
) -> WorkerPool:
    """Build a WorkerPool whose workers optionally fail."""
    fail = fail or set()
    names = agents or ["frontend", "backend", "database", "routing"]
    workers = {
        name: MockWorkerAgent(name, should_fail=(name in fail))
        for name in names
    }
    return WorkerPool(workers)


# ---------------------------------------------------------------------------
# Tests — DAG / dependency analysis
# ---------------------------------------------------------------------------


def test_dag_no_dependencies() -> None:
    """Tasks with no deps all land in a single batch."""
    tasks = [_task("t1"), _task("t2"), _task("t3")]
    batches = build_execution_batches(tasks)
    assert len(batches) == 1
    assert set(batches[0].task_ids) == {"t1", "t2", "t3"}


def test_dag_linear_chain() -> None:
    """t1 → t2 → t3 must produce three sequential batches."""
    tasks = [
        _task("t1"),
        _task("t2", deps=["t1"]),
        _task("t3", deps=["t2"]),
    ]
    batches = build_execution_batches(tasks)
    assert len(batches) == 3
    assert batches[0].task_ids == ["t1"]
    assert batches[1].task_ids == ["t2"]
    assert batches[2].task_ids == ["t3"]


def test_dag_parallel_after_root() -> None:
    """t2 and t3 both depend on t1 — they must share a batch."""
    tasks = [
        _task("t1"),
        _task("t2", deps=["t1"]),
        _task("t3", deps=["t1"]),
    ]
    batches = build_execution_batches(tasks)
    assert len(batches) == 2
    assert batches[0].task_ids == ["t1"]
    assert set(batches[1].task_ids) == {"t2", "t3"}


def test_dag_diamond() -> None:
    """Classic diamond: t1 → {t2, t3} → t4."""
    tasks = [
        _task("t1"),
        _task("t2", deps=["t1"]),
        _task("t3", deps=["t1"]),
        _task("t4", deps=["t2", "t3"]),
    ]
    batches = build_execution_batches(tasks)
    assert len(batches) == 3
    assert batches[0].task_ids == ["t1"]
    assert set(batches[1].task_ids) == {"t2", "t3"}
    assert batches[2].task_ids == ["t4"]


def test_dag_batch_index() -> None:
    """batch_index must be 0-based and correct."""
    tasks = [_task("t1"), _task("t2", deps=["t1"])]
    batches = build_execution_batches(tasks)
    assert batches[0].batch_index == 0
    assert batches[1].batch_index == 1


# ---------------------------------------------------------------------------
# Tests — Cycle detection
# ---------------------------------------------------------------------------


def test_cycle_direct() -> None:
    """t1 → t2 → t1 must raise CyclicDependencyError."""
    tasks = [_task("t1", deps=["t2"]), _task("t2", deps=["t1"])]
    with pytest.raises(CyclicDependencyError):
        build_execution_batches(tasks)


def test_cycle_three_node() -> None:
    """t1→t2→t3→t1 is cyclic."""
    tasks = [
        _task("t1", deps=["t3"]),
        _task("t2", deps=["t1"]),
        _task("t3", deps=["t2"]),
    ]
    with pytest.raises(CyclicDependencyError):
        build_execution_batches(tasks)


def test_missing_dependency_raises() -> None:
    """Referencing a non-existent dep must raise ExecutionPlanError."""
    tasks = [_task("t1", deps=["ghost"])]
    with pytest.raises(ExecutionPlanError):
        build_execution_batches(tasks)


# ---------------------------------------------------------------------------
# Tests — dependency_map and agent_map helpers
# ---------------------------------------------------------------------------


def test_build_dependency_map() -> None:
    tasks = [_task("t1"), _task("t2", deps=["t1"])]
    dep_map = build_dependency_map(tasks)
    assert dep_map == {"t1": [], "t2": ["t1"]}


def test_build_agent_map() -> None:
    tasks = [
        _task("t1", agent=TaskAssignedAgent.FRONTEND),
        _task("t2", agent=TaskAssignedAgent.BACKEND),
    ]
    agent_map = build_agent_map(tasks)
    assert agent_map == {"t1": "frontend", "t2": "backend"}


# ---------------------------------------------------------------------------
# Tests — WorkerPool
# ---------------------------------------------------------------------------


def test_worker_pool_runs_task() -> None:
    """WorkerPool must return COMPLETED result with artifact_id."""
    task = _task("t1", agent=TaskAssignedAgent.BACKEND)
    pool = _pool()
    result = asyncio.run(pool.run_task(task))
    assert result.status == TaskExecutionStatus.COMPLETED
    assert result.artifact_id == "art_t1_1"
    assert result.task_id == "t1"


def test_worker_pool_handles_failure() -> None:
    """WorkerPool must return FAILED result, not raise."""
    task = _task("t1", agent=TaskAssignedAgent.BACKEND)
    pool = _pool(fail={"backend"})
    result = asyncio.run(pool.run_task(task))
    assert result.status == TaskExecutionStatus.FAILED
    assert result.error is not None
    assert result.artifact_id is None


def test_worker_pool_skips_unknown_agent() -> None:
    """WorkerPool must return SKIPPED for unregistered agent."""
    task = _task("t1", agent=TaskAssignedAgent.QA)
    pool = _pool()  # no qa worker
    result = asyncio.run(pool.run_task(task))
    assert result.status == TaskExecutionStatus.SKIPPED


def test_worker_pool_runs_batch_concurrently() -> None:
    """run_batch must return results for all tasks."""
    tasks = [
        _task("t1", agent=TaskAssignedAgent.BACKEND),
        _task("t2", agent=TaskAssignedAgent.FRONTEND),
        _task("t3", agent=TaskAssignedAgent.DATABASE),
    ]
    pool = _pool()
    results = asyncio.run(pool.run_batch(tasks))
    assert len(results) == 3
    assert all(r.status == TaskExecutionStatus.COMPLETED for r in results)


# ---------------------------------------------------------------------------
# Tests — ExecutionCoordinator
# ---------------------------------------------------------------------------


def test_coordinator_empty_tasks(tmp_path: Path) -> None:
    """Coordinator must handle empty task plan without crashing."""
    sm = _sm(tmp_path)
    coordinator = ExecutionCoordinator(sm, worker_pool=_pool())
    report = asyncio.run(coordinator.execute_all())
    assert report.total_tasks == 0
    assert report.status == ExecutionRunStatus.EMPTY


def test_coordinator_executes_all_independent_tasks(tmp_path: Path) -> None:
    """Independent tasks must all complete successfully."""
    sm = _sm(tmp_path)
    tasks = [
        _task("t1", agent=TaskAssignedAgent.BACKEND),
        _task("t2", agent=TaskAssignedAgent.FRONTEND),
        _task("t3", agent=TaskAssignedAgent.DATABASE),
    ]
    sm.save_tasks(TaskPlan(tasks=tasks))
    coordinator = ExecutionCoordinator(sm, worker_pool=_pool())
    report = asyncio.run(coordinator.execute_all())
    assert report.completed_tasks == 3
    assert report.failed_tasks == 0
    assert report.skipped_tasks == 0
    assert report.total_batches == 1
    assert report.status == ExecutionRunStatus.SUCCESS


def test_coordinator_respects_dependency_order(tmp_path: Path) -> None:
    """Tasks must be dispatched batch-by-batch, respecting deps."""
    sm = _sm(tmp_path)
    tasks = [
        _task("db", agent=TaskAssignedAgent.DATABASE),
        _task("api", agent=TaskAssignedAgent.BACKEND, deps=["db"]),
        _task("ui", agent=TaskAssignedAgent.FRONTEND, deps=["api"]),
    ]
    sm.save_tasks(TaskPlan(tasks=tasks))
    coordinator = ExecutionCoordinator(sm, worker_pool=_pool())
    report = asyncio.run(coordinator.execute_all())
    assert report.completed_tasks == 3
    assert report.total_batches == 3
    assert report.status == ExecutionRunStatus.SUCCESS


def test_coordinator_parallel_batch(tmp_path: Path) -> None:
    """Tasks in the same batch all complete and come from one batch."""
    sm = _sm(tmp_path)
    tasks = [
        _task("root", agent=TaskAssignedAgent.DATABASE),
        _task("a", agent=TaskAssignedAgent.BACKEND, deps=["root"]),
        _task("b", agent=TaskAssignedAgent.FRONTEND, deps=["root"]),
        _task("c", agent=TaskAssignedAgent.ROUTING, deps=["root"]),
    ]
    sm.save_tasks(TaskPlan(tasks=tasks))
    coordinator = ExecutionCoordinator(sm, worker_pool=_pool())
    report = asyncio.run(coordinator.execute_all())
    assert report.completed_tasks == 4
    assert report.total_batches == 2
    assert report.status == ExecutionRunStatus.SUCCESS


# ---------------------------------------------------------------------------
# Tests — Failure handling
# ---------------------------------------------------------------------------


def test_coordinator_failed_task_marks_dependents_skipped(tmp_path: Path) -> None:
    """If the db task fails, the api task depending on it must be skipped."""
    sm = _sm(tmp_path)
    tasks = [
        _task("db", agent=TaskAssignedAgent.DATABASE),
        _task("api", agent=TaskAssignedAgent.BACKEND, deps=["db"]),
    ]
    sm.save_tasks(TaskPlan(tasks=tasks))
    pool = _pool(fail={"database"})
    coordinator = ExecutionCoordinator(sm, worker_pool=pool)
    report = asyncio.run(coordinator.execute_all())
    assert report.failed_tasks == 1
    assert report.skipped_tasks == 1
    assert report.completed_tasks == 0
    assert report.status == ExecutionRunStatus.FAILED


def test_coordinator_partial_success(tmp_path: Path) -> None:
    """Independent tasks continue even if one agent fails."""
    sm = _sm(tmp_path)
    tasks = [
        _task("db", agent=TaskAssignedAgent.DATABASE),
        _task("fe", agent=TaskAssignedAgent.FRONTEND),  # no dep on db
    ]
    sm.save_tasks(TaskPlan(tasks=tasks))
    pool = _pool(fail={"database"})
    coordinator = ExecutionCoordinator(sm, worker_pool=pool)
    report = asyncio.run(coordinator.execute_all())
    assert report.failed_tasks == 1
    assert report.completed_tasks == 1
    assert report.status == ExecutionRunStatus.PARTIAL


def test_coordinator_does_not_crash_on_task_failure(tmp_path: Path) -> None:
    """An agent raising an exception must not crash execute_all()."""
    sm = _sm(tmp_path)
    sm.save_tasks(TaskPlan(tasks=[_task("t1", agent=TaskAssignedAgent.BACKEND)]))
    pool = _pool(fail={"backend"})
    coordinator = ExecutionCoordinator(sm, worker_pool=pool)
    report = asyncio.run(coordinator.execute_all())  # must not raise
    assert report.failed_tasks == 1


# ---------------------------------------------------------------------------
# Tests — Cycle / invalid plan rejection
# ---------------------------------------------------------------------------


def test_coordinator_rejects_cyclic_plan(tmp_path: Path) -> None:
    """Coordinator must raise CyclicDependencyError before running any tasks."""
    sm = _sm(tmp_path)
    tasks = [
        _task("t1", deps=["t2"]),
        _task("t2", deps=["t1"]),
    ]
    sm.save_tasks(TaskPlan(tasks=tasks))
    coordinator = ExecutionCoordinator(sm, worker_pool=_pool())
    with pytest.raises(CyclicDependencyError):
        asyncio.run(coordinator.execute_all())


def test_coordinator_rejects_missing_dependency(tmp_path: Path) -> None:
    """Coordinator must raise ExecutionPlanError for unknown dep ID."""
    sm = _sm(tmp_path)
    sm.save_tasks(TaskPlan(tasks=[_task("t1", deps=["ghost"])]))
    coordinator = ExecutionCoordinator(sm, worker_pool=_pool())
    with pytest.raises(ExecutionPlanError):
        asyncio.run(coordinator.execute_all())


# ---------------------------------------------------------------------------
# Tests — Persistence
# ---------------------------------------------------------------------------


def test_execution_plan_persisted(tmp_path: Path) -> None:
    """ExecutionPlan must be saved to .project/execution/."""
    sm = _sm(tmp_path)
    sm.save_tasks(TaskPlan(tasks=[_task("t1")]))
    coordinator = ExecutionCoordinator(sm, worker_pool=_pool())
    asyncio.run(coordinator.execute_all())

    plan = sm.load_execution_plan()
    assert plan.total_tasks == 1
    assert len(plan.batches) == 1


def test_execution_report_persisted(tmp_path: Path) -> None:
    """ExecutionReport must be saved and loadable."""
    sm = _sm(tmp_path)
    sm.save_tasks(TaskPlan(tasks=[_task("t1")]))
    coordinator = ExecutionCoordinator(sm, worker_pool=_pool())
    asyncio.run(coordinator.execute_all())

    report = sm.load_execution_report()
    assert report.completed_tasks == 1
    assert report.status == ExecutionRunStatus.SUCCESS


def test_execution_history_grows_across_runs(tmp_path: Path) -> None:
    """Each execute_all call must append a new entry to history."""
    sm = _sm(tmp_path)
    sm.save_tasks(TaskPlan(tasks=[_task("t1")]))
    pool = _pool()
    coordinator = ExecutionCoordinator(sm, worker_pool=pool)

    asyncio.run(coordinator.execute_all())
    asyncio.run(coordinator.execute_all())

    history = sm.load_execution_history()
    assert len(history.runs) == 2


def test_execution_report_archived_by_run_id(tmp_path: Path) -> None:
    """Each run must produce an archived report file."""
    sm = _sm(tmp_path)
    sm.save_tasks(TaskPlan(tasks=[_task("t1")]))
    coordinator = ExecutionCoordinator(sm, worker_pool=_pool())
    report = asyncio.run(coordinator.execute_all())

    archived = sm.execution_dir / f"execution_report.{report.run_id}.json"
    assert archived.exists()


def test_execution_history_never_overwritten(tmp_path: Path) -> None:
    """History must accumulate across 3 runs."""
    sm = _sm(tmp_path)
    sm.save_tasks(TaskPlan(tasks=[_task("t1")]))
    pool = _pool()
    coordinator = ExecutionCoordinator(sm, worker_pool=pool)
    for _ in range(3):
        asyncio.run(coordinator.execute_all())

    history = sm.load_execution_history()
    assert len(history.runs) == 3


# ---------------------------------------------------------------------------
# Tests — ExecutionHistory model
# ---------------------------------------------------------------------------


def test_execution_history_run_id_increments() -> None:
    history = ExecutionHistory(project_name="X")
    assert history.get_next_run_id() == "run_0001"
    from omnix_cli.schemas.execution import ExecutionHistoryEntry, ExecutionRunStatus
    history.runs.append(
        ExecutionHistoryEntry(
            run_id="run_0001",
            total_tasks=1,
            completed_tasks=1,
            failed_tasks=0,
            skipped_tasks=0,
            artifacts_generated=1,
            duration_seconds=0.1,
            status=ExecutionRunStatus.SUCCESS,
        )
    )
    assert history.get_next_run_id() == "run_0002"


# ---------------------------------------------------------------------------
# Tests — ExecutionReport helpers
# ---------------------------------------------------------------------------


def test_completion_rate_zero_tasks() -> None:
    from datetime import datetime
    from omnix_cli.schemas.execution import ExecutionReport, ExecutionRunStatus, ExecutionStrategy
    report = ExecutionReport(
        project_name="X",
        run_id="r1",
        started_at=datetime.now(),
        strategy=ExecutionStrategy.PARALLEL,
        total_tasks=0,
        completed_tasks=0,
        failed_tasks=0,
        skipped_tasks=0,
        total_batches=0,
        artifacts_generated=0,
        status=ExecutionRunStatus.EMPTY,
    )
    assert report.completion_rate == 0.0


def test_completion_rate_partial() -> None:
    from datetime import datetime
    from omnix_cli.schemas.execution import ExecutionReport, ExecutionRunStatus, ExecutionStrategy
    report = ExecutionReport(
        project_name="X",
        run_id="r1",
        started_at=datetime.now(),
        strategy=ExecutionStrategy.PARALLEL,
        total_tasks=4,
        completed_tasks=3,
        failed_tasks=1,
        skipped_tasks=0,
        total_batches=2,
        artifacts_generated=3,
        status=ExecutionRunStatus.PARTIAL,
    )
    assert report.completion_rate == 75.0


# ---------------------------------------------------------------------------
# Tests — CLI smoke tests
# ---------------------------------------------------------------------------


def test_execute_all_cli_success(tmp_path: Path) -> None:
    from typer.testing import CliRunner
    from omnix_cli.cli.main import app
    import omnix_cli.agents.coordinator.coordinator as coord_module

    sm = _sm(tmp_path)
    tasks = [
        _task("t1", agent=TaskAssignedAgent.BACKEND),
        _task("t2", agent=TaskAssignedAgent.FRONTEND),
    ]
    sm.save_tasks(TaskPlan(tasks=tasks))

    original = coord_module.build_default_provider_registry
    coord_module.build_default_provider_registry = lambda _: None  # type: ignore[assignment]

    original_pool = ExecutionCoordinator._build_worker_pool

    def _mock_pool(self: ExecutionCoordinator) -> WorkerPool:
        return _pool()

    ExecutionCoordinator._build_worker_pool = _mock_pool  # type: ignore[method-assign]

    try:
        runner = CliRunner()
        result = runner.invoke(app, ["execute-all", "-w", str(tmp_path)])
        assert result.exit_code == 0, result.output
        assert "Execution Complete" in result.output
        assert "Completed:" in result.output
    finally:
        coord_module.build_default_provider_registry = original  # type: ignore[assignment]
        ExecutionCoordinator._build_worker_pool = original_pool  # type: ignore[method-assign]


def test_execute_all_cli_cyclic_error(tmp_path: Path) -> None:
    from typer.testing import CliRunner
    from omnix_cli.cli.main import app

    sm = _sm(tmp_path)
    tasks = [_task("t1", deps=["t2"]), _task("t2", deps=["t1"])]
    sm.save_tasks(TaskPlan(tasks=tasks))

    runner = CliRunner()
    result = runner.invoke(app, ["execute-all", "-w", str(tmp_path)])
    assert result.exit_code == 1
    assert "Cyclic" in result.output or "Cyclic" in (result.stderr or "")


def test_execution_display_no_report(tmp_path: Path) -> None:
    from typer.testing import CliRunner
    from omnix_cli.cli.main import app

    _sm(tmp_path)
    runner = CliRunner()
    result = runner.invoke(app, ["execution", "-w", str(tmp_path)])
    assert result.exit_code == 1
    assert "Execution report not found" in result.output


def test_execution_display_after_run(tmp_path: Path) -> None:
    from typer.testing import CliRunner
    from omnix_cli.cli.main import app
    import omnix_cli.agents.coordinator.coordinator as coord_module

    sm = _sm(tmp_path)
    sm.save_tasks(TaskPlan(tasks=[_task("t1")]))

    original_pool = ExecutionCoordinator._build_worker_pool

    def _mock_pool(self: ExecutionCoordinator) -> WorkerPool:
        return _pool()

    ExecutionCoordinator._build_worker_pool = _mock_pool  # type: ignore[method-assign]

    try:
        runner = CliRunner()
        runner.invoke(app, ["execute-all", "-w", str(tmp_path)])
        result = runner.invoke(app, ["execution", "-w", str(tmp_path)])
        assert result.exit_code == 0, result.output
        assert "Execution Status" in result.output
        assert "Tasks Executed" in result.output
    finally:
        ExecutionCoordinator._build_worker_pool = original_pool  # type: ignore[method-assign]
