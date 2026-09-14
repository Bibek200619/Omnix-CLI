"""Schemas for Phase 10 autonomous build orchestration."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from omnix_cli.schemas.artifacts import Artifact
from omnix_cli.schemas.blueprint import ProjectBlueprint
from omnix_cli.schemas.execution import ExecutionHistory
from omnix_cli.schemas.integration import IntegratedPackage
from omnix_cli.schemas.qa import (
    CoverageReport,
    GapReport,
    QASummary,
    QualityReport,
    RiskReport,
)
from omnix_cli.schemas.repair import RepairHistory
from omnix_cli.schemas.tasks import TaskPlan


class BuildStatus(StrEnum):
    """Lifecycle state of one autonomous build run."""

    PENDING = "pending"
    RUNNING = "running"
    REPAIRING = "repairing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BuildOutcome(StrEnum):
    """Terminal build outcome used for reports and summaries."""

    INCOMPLETE = "INCOMPLETE"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class BuildStopReason(StrEnum):
    """Reason the autonomous lifecycle stopped."""

    QUALITY_THRESHOLD_REACHED = "quality_threshold_reached"
    MAX_REPAIR_CYCLES_REACHED = "max_repair_cycles_reached"
    FATAL_FAILURE = "fatal_failure"
    MANUAL_STOP = "manual_stop"


class BuildPhase(StrEnum):
    """Coarse-grained phases coordinated by the build orchestrator."""

    CREATE_GOAL = "create_goal"
    ARCHITECT = "architect"
    PLAN = "plan"
    EXECUTE = "execute"
    INTEGRATE = "integrate"
    QA = "qa"
    QUALITY_CHECK = "quality_check"
    REPAIR = "repair"
    FINALIZE = "finalize"
    RECOVERY = "recovery"


class BuildPhaseStatus(StrEnum):
    """Status for a single phase execution record."""

    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class BuildConfig(BaseModel):
    """User-configurable autonomous build policy."""

    model_config = ConfigDict(extra="forbid")

    quality_threshold: int = Field(default=90, ge=0, le=100)
    max_repair_cycles: int = Field(default=3, ge=0)


class BuildBlueprintSummary(BaseModel):
    """Compact blueprint metrics for reports."""

    model_config = ConfigDict(extra="forbid")

    project_name: str = ""
    description: str = ""
    feature_count: int = 0
    entity_count: int = 0
    module_count: int = 0
    page_count: int = 0
    api_count: int = 0
    architecture_note_count: int = 0


class BuildExecutionStatistics(BaseModel):
    """Execution totals across all execute-all runs in a build run."""

    model_config = ConfigDict(extra="forbid")

    total_runs: int = 0
    latest_run_id: str | None = None
    total_tasks_executed: int = 0
    total_completed_tasks: int = 0
    total_failed_tasks: int = 0
    total_skipped_tasks: int = 0
    artifacts_generated: int = 0
    total_duration_seconds: float = 0.0


class BuildIntegrationResult(BaseModel):
    """Latest integration result recorded by a build run."""

    model_config = ConfigDict(extra="forbid")

    status: str
    artifacts_processed: int
    dependencies_found: int
    conflicts_found: int
    coverage_status: str
    summary: str = ""


class BuildQAResult(BaseModel):
    """Latest QA result recorded by a build run."""

    model_config = ConfigDict(extra="forbid")

    version: int
    quality_score: int
    coverage_score: int
    gap_score: int
    risk_score: int
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    status: str


class BuildFailure(BaseModel):
    """Failure captured during a build run."""

    model_config = ConfigDict(extra="forbid")

    phase: BuildPhase
    error_type: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)


class BuildDecision(BaseModel):
    """Decision made by the autonomous orchestrator."""

    model_config = ConfigDict(extra="forbid")

    phase: BuildPhase
    decision: str
    rationale: str
    timestamp: datetime = Field(default_factory=datetime.now)
    data: dict[str, Any] = Field(default_factory=dict)


class BuildPhaseResult(BaseModel):
    """Audit record for one phase execution."""

    model_config = ConfigDict(extra="forbid")

    phase: BuildPhase
    status: BuildPhaseStatus
    started_at: datetime = Field(default_factory=datetime.now)
    finished_at: datetime | None = None
    duration_seconds: float = 0.0
    summary: str = ""
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class BuildReport(BaseModel):
    """Top-level report for one autonomous build run."""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    goal: str
    status: BuildStatus = BuildStatus.PENDING
    outcome: BuildOutcome = BuildOutcome.INCOMPLETE
    started_at: datetime = Field(default_factory=datetime.now)
    finished_at: datetime | None = None
    duration_seconds: float = 0.0
    quality_threshold: int = 90
    max_repair_cycles: int = 3
    repair_cycles: int = 0
    final_quality_score: int | None = None
    completion_reason: BuildStopReason | None = None
    blueprint_summary: BuildBlueprintSummary = Field(
        default_factory=BuildBlueprintSummary
    )
    task_count: int = 0
    artifacts_generated: int = 0
    integration_result: BuildIntegrationResult | None = None
    qa_result: BuildQAResult | None = None
    execution_statistics: BuildExecutionStatistics = Field(
        default_factory=BuildExecutionStatistics
    )
    phase_results: list[BuildPhaseResult] = Field(default_factory=list)
    decisions: list[BuildDecision] = Field(default_factory=list)
    failures: list[BuildFailure] = Field(default_factory=list)

    @field_validator("goal")
    @classmethod
    def validate_goal(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            msg = "Build goal cannot be empty."
            raise ValueError(msg)
        return normalized


class BuildHistoryEntry(BaseModel):
    """One row in the append-only build history."""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    goal: str
    started_at: datetime
    finished_at: datetime | None = None
    duration_seconds: float = 0.0
    status: BuildStatus
    outcome: BuildOutcome
    quality_score: int | None = None
    repair_cycles: int = 0
    artifacts_generated: int = 0
    completion_reason: BuildStopReason | None = None


class BuildHistory(BaseModel):
    """Persisted audit history of autonomous build runs."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = "10.0"
    runs: list[BuildHistoryEntry] = Field(default_factory=list)

    def get_next_run_number(self) -> int:
        """Return the next monotonically increasing build number."""

        if not self.runs:
            return 1

        numbers: list[int] = []
        for run in self.runs:
            if run.run_id.startswith("build_"):
                suffix = run.run_id.removeprefix("build_")
                if suffix.isdigit():
                    numbers.append(int(suffix))
        if not numbers:
            return len(self.runs) + 1
        return max(numbers) + 1


class BuildMetadata(BaseModel):
    """Build metadata embedded in the final project package."""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    goal: str
    status: BuildStatus
    outcome: BuildOutcome
    quality_threshold: int
    max_repair_cycles: int
    repair_cycles: int
    final_quality_score: int | None = None
    completion_reason: BuildStopReason | None = None
    started_at: datetime
    finished_at: datetime | None = None
    duration_seconds: float = 0.0


class BuildQAReports(BaseModel):
    """All latest QA reports included in the final package."""

    model_config = ConfigDict(extra="forbid")

    summary: QASummary
    quality: QualityReport
    coverage: CoverageReport
    gap: GapReport
    risk: RiskReport


class FinalProjectPackage(BaseModel):
    """Final representation of a build run."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = "10.0"
    generated_at: datetime = Field(default_factory=datetime.now)
    build_metadata: BuildMetadata
    blueprint: ProjectBlueprint
    tasks: TaskPlan
    artifacts: list[Artifact] = Field(default_factory=list)
    integrated_package: IntegratedPackage | None = None
    qa_reports: BuildQAReports | None = None
    repair_history: RepairHistory | None = None
    execution_history: ExecutionHistory | None = None
    build_report: BuildReport
