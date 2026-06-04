"""Tests for Phase 8: Repair Agent."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from omnix_cli.agents.repair.agent import RepairAgent
from omnix_cli.core.state_manager import StateManager
from omnix_cli.providers.base import BaseProvider
from omnix_cli.providers.registry import ProviderRegistry
from omnix_cli.schemas.qa import (
    CoverageReport,
    GapReport,
    QAStatus,
    QASummary,
    QualityReport,
    RiskReport,
)
from omnix_cli.schemas.repair import (
    RepairHistory,
    RepairSeverity,
    RepairStatus,
)
from omnix_cli.schemas.tasks import AgentRole

# ---------------------------------------------------------------------------
# Mock provider
# ---------------------------------------------------------------------------


class MockRepairProvider(BaseProvider):
    """Deterministic mock provider for repair testing."""

    response: str = ""

    @property
    def provider_name(self) -> str:
        return "mock"

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.2,
    ) -> str:
        return type(self).response


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _initialized_state(tmp_path: Path) -> StateManager:
    """Create a StateManager with a fully initialized project including QA reports."""
    sm = StateManager(tmp_path)
    sm.init_project(project_name="Test Repair Project")
    sm.save_models(
        sm.load_models().with_assignment(
            AgentRole.MASTER, provider="mock", model="master-model"
        )
    )
    return sm


def _seed_qa_reports(sm: StateManager, *, quality_score: int = 72) -> None:
    """Persist minimal QA reports so the repair agent can read them."""
    findings = [
        {
            "id": "QA-Q-001",
            "title": "Customer API missing",
            "description": "The Customer CRUD API is not implemented.",
            "severity": "critical",
            "category": "Coverage",
            "explanation": "Blueprint specifies Customer API but no artifact exists.",
        },
        {
            "id": "QA-Q-002",
            "title": "Auth token expiry too long",
            "description": "JWT tokens expire after 30 days.",
            "severity": "high",
            "category": "Security",
            "explanation": "Industry standard is 1 hour for access tokens.",
        },
        {
            "id": "QA-Q-003",
            "title": "Missing pagination on list endpoints",
            "description": "GET /items returns unbounded lists.",
            "severity": "medium",
            "category": "Architecture",
            "explanation": "Large datasets will cause slow responses.",
        },
        {
            "id": "QA-Q-004",
            "title": "Minor docs typo",
            "description": "Typo in API documentation.",
            "severity": "low",
            "category": "Documentation",
            "explanation": "Non-critical cosmetic issue.",
        },
    ]
    summary = QASummary(
        project_name="Test Repair Project",
        version=1,
        quality_score=quality_score,
        coverage_score=70,
        gap_score=80,
        risk_score=85,
        critical_issues=1,
        high_issues=1,
        medium_issues=1,
        low_issues=1,
        status=QAStatus.REVIEW_REQUIRED,
    )
    quality = QualityReport(
        project_name="Test Repair Project",
        version=1,
        overall_score=quality_score,
        critical_issues=1,
        high_issues=1,
        medium_issues=1,
        low_issues=1,
        findings=findings,  # type: ignore[arg-type]
        status=QAStatus.REVIEW_REQUIRED,
        summary="Issues found.",
    )
    coverage = CoverageReport(
        project_name="Test Repair Project",
        version=1,
        coverage_score=70,
        missing_apis=["Customer CRUD API"],
    )
    gap = GapReport(project_name="Test Repair Project", version=1, gap_score=80)
    risk = RiskReport(project_name="Test Repair Project", version=1, risk_score=85)
    sm.save_qa_reports(
        summary=summary, quality=quality, coverage=coverage, gap=gap, risk=risk
    )


def _mock_registry() -> ProviderRegistry:
    registry = ProviderRegistry()
    registry.register("mock", MockRepairProvider)
    return registry


def _repair_response(cycle: int = 1) -> str:
    """Build a deterministic repair agent JSON response."""
    return json.dumps(
        {
            "repair_plan": {
                "items": [
                    {
                        "id": f"repair_{cycle:03d}_001",
                        "severity": "critical",
                        "issue": "Customer API missing",
                        "strategy": "Generate backend API artifact for Customer CRUD",
                        "target_agent": "backend",
                        "qa_finding_id": "QA-Q-001",
                        "status": "planned",
                    },
                    {
                        "id": f"repair_{cycle:03d}_002",
                        "severity": "high",
                        "issue": "Auth token expiry too long",
                        "strategy": "Update backend auth configuration artifact",
                        "target_agent": "backend",
                        "qa_finding_id": "QA-Q-002",
                        "status": "planned",
                    },
                    {
                        "id": f"repair_{cycle:03d}_003",
                        "severity": "medium",
                        "issue": "Missing pagination on list endpoints",
                        "strategy": "Add pagination design to backend API artifact",
                        "target_agent": "backend",
                        "qa_finding_id": "QA-Q-003",
                        "status": "planned",
                    },
                    {
                        "id": f"repair_{cycle:03d}_004",
                        "severity": "low",
                        "issue": "Minor docs typo",
                        "strategy": "Correct typo in documentation artifact",
                        "target_agent": "backend",
                        "qa_finding_id": "QA-Q-004",
                        "status": "planned",
                    },
                ]
            },
            "repair_artifacts": [
                {
                    "id": f"repair_artifact_{cycle:03d}_001",
                    "repair_plan_id": f"repair_{cycle:03d}_001",
                    "qa_finding_id": "QA-Q-001",
                    "target_agent": "backend",
                    "title": "Customer CRUD API Repair Specification",
                    "description": "Defines all Customer CRUD endpoints.",
                    "content": (
                        "GET /customers, POST /customers, PUT /customers/{id}, "
                        "DELETE /customers/{id}"
                    ),
                },
                {
                    "id": f"repair_artifact_{cycle:03d}_002",
                    "repair_plan_id": f"repair_{cycle:03d}_002",
                    "qa_finding_id": "QA-Q-002",
                    "target_agent": "backend",
                    "title": "Auth Token Expiry Repair",
                    "description": "Reduces JWT access token expiry to 1 hour.",
                    "content": "JWT_ACCESS_EXPIRY=3600",
                },
            ],
            "repair_report": {
                "expected_impact": (
                    f"Cycle {cycle}: resolving critical + high issues should "
                    "raise score above 85."
                )
            },
        }
    )


# ---------------------------------------------------------------------------
# Tests — Repair Planning
# ---------------------------------------------------------------------------


def test_repair_agent_generates_plan(tmp_path: Path) -> None:
    """Repair agent must generate a structured repair plan from QA findings."""
    sm = _initialized_state(tmp_path)
    _seed_qa_reports(sm)
    MockRepairProvider.response = _repair_response()

    result = asyncio.run(RepairAgent(sm, provider_registry=_mock_registry()).repair())

    plan = result.repair_plan
    assert len(plan.items) == 4
    assert plan.cycle == 1
    assert plan.project_name == "Test Repair Project"


def test_repair_plan_severity_prioritization(tmp_path: Path) -> None:
    """Plan items must be sorted critical → high → medium → low."""
    sm = _initialized_state(tmp_path)
    _seed_qa_reports(sm)
    MockRepairProvider.response = _repair_response()

    result = asyncio.run(RepairAgent(sm, provider_registry=_mock_registry()).repair())

    severities = [item.severity for item in result.repair_plan.items]
    assert severities == [
        RepairSeverity.CRITICAL,
        RepairSeverity.HIGH,
        RepairSeverity.MEDIUM,
        RepairSeverity.LOW,
    ]


def test_repair_plan_item_fields(tmp_path: Path) -> None:
    """Each repair plan item must have required traceability fields."""
    sm = _initialized_state(tmp_path)
    _seed_qa_reports(sm)
    MockRepairProvider.response = _repair_response()

    result = asyncio.run(RepairAgent(sm, provider_registry=_mock_registry()).repair())

    critical_item = result.repair_plan.items[0]
    assert critical_item.severity == RepairSeverity.CRITICAL
    assert critical_item.qa_finding_id == "QA-Q-001"
    assert critical_item.target_agent == "backend"
    assert critical_item.status == RepairStatus.PLANNED
    assert critical_item.issue != ""
    assert critical_item.strategy != ""


# ---------------------------------------------------------------------------
# Tests — Repair Artifact Generation
# ---------------------------------------------------------------------------


def test_repair_artifacts_generated(tmp_path: Path) -> None:
    """Repair agent must generate repair artifacts."""
    sm = _initialized_state(tmp_path)
    _seed_qa_reports(sm)
    MockRepairProvider.response = _repair_response()

    result = asyncio.run(RepairAgent(sm, provider_registry=_mock_registry()).repair())

    assert len(result.repair_artifacts) == 2
    art = result.repair_artifacts[0]
    assert art.repair_plan_id.startswith("repair_")
    assert art.qa_finding_id == "QA-Q-001"
    assert art.title != ""
    assert art.content != ""
    assert art.cycle == 1


def test_repair_artifacts_reference_plan_items(tmp_path: Path) -> None:
    """Every repair artifact must reference a valid repair plan item ID."""
    sm = _initialized_state(tmp_path)
    _seed_qa_reports(sm)
    MockRepairProvider.response = _repair_response()

    result = asyncio.run(RepairAgent(sm, provider_registry=_mock_registry()).repair())

    plan_ids = {item.id for item in result.repair_plan.items}
    for artifact in result.repair_artifacts:
        assert artifact.repair_plan_id in plan_ids


# ---------------------------------------------------------------------------
# Tests — Repair Report
# ---------------------------------------------------------------------------


def test_repair_report_fields(tmp_path: Path) -> None:
    """Repair report must contain correct counts and status."""
    sm = _initialized_state(tmp_path)
    _seed_qa_reports(sm)
    MockRepairProvider.response = _repair_response()

    result = asyncio.run(RepairAgent(sm, provider_registry=_mock_registry()).repair())

    report = result.repair_report
    assert report.issues_processed == 4
    assert report.critical_count == 1
    assert report.high_count == 1
    assert report.medium_count == 1
    assert report.low_count == 1
    assert report.artifacts_generated == 2
    assert report.status == "COMPLETE"
    assert report.expected_impact != ""
    assert len(report.plan_item_ids) == 4
    assert len(report.repair_artifact_ids) == 2


# ---------------------------------------------------------------------------
# Tests — Repair Persistence
# ---------------------------------------------------------------------------


def test_repair_plan_persisted(tmp_path: Path) -> None:
    """Repair plan must be saved to .project/repair/repair_plan.json."""
    sm = _initialized_state(tmp_path)
    _seed_qa_reports(sm)
    MockRepairProvider.response = _repair_response()

    asyncio.run(RepairAgent(sm, provider_registry=_mock_registry()).repair())

    assert (sm.repair_dir / "repair_plan.json").exists()
    loaded = sm.load_repair_plan()
    assert loaded.cycle == 1
    assert len(loaded.items) == 4


def test_repair_artifacts_persisted(tmp_path: Path) -> None:
    """Repair artifacts must be saved to .project/repair/."""
    sm = _initialized_state(tmp_path)
    _seed_qa_reports(sm)
    MockRepairProvider.response = _repair_response()

    asyncio.run(RepairAgent(sm, provider_registry=_mock_registry()).repair())

    artifacts = sm.list_repair_artifacts()
    assert len(artifacts) == 2


def test_repair_report_persisted(tmp_path: Path) -> None:
    """Repair report must be saved to .project/repair/repair_report.json."""
    sm = _initialized_state(tmp_path)
    _seed_qa_reports(sm)
    MockRepairProvider.response = _repair_response()

    asyncio.run(RepairAgent(sm, provider_registry=_mock_registry()).repair())

    assert (sm.repair_dir / "repair_report.json").exists()
    loaded = sm.load_repair_report()
    assert loaded.cycle == 1
    assert loaded.status == "COMPLETE"


def test_repair_history_persisted(tmp_path: Path) -> None:
    """Repair history must be saved and contain the cycle entry."""
    sm = _initialized_state(tmp_path)
    _seed_qa_reports(sm)
    MockRepairProvider.response = _repair_response()

    asyncio.run(RepairAgent(sm, provider_registry=_mock_registry()).repair())

    history = sm.load_repair_history()
    assert len(history.cycles) == 1
    assert history.cycles[0].cycle == 1
    assert history.cycles[0].issues_addressed == 4
    assert history.cycles[0].artifacts_generated == 2
    assert history.cycles[0].quality_score_before == 72
    assert history.cycles[0].status == "COMPLETE"


# ---------------------------------------------------------------------------
# Tests — Repair History across multiple cycles
# ---------------------------------------------------------------------------


def test_multiple_repair_cycles_preserved(tmp_path: Path) -> None:
    """Running repair twice must create cycle 1 and cycle 2; history must grow."""
    sm = _initialized_state(tmp_path)
    _seed_qa_reports(sm)
    registry = _mock_registry()

    # Cycle 1
    MockRepairProvider.response = _repair_response(1)
    asyncio.run(RepairAgent(sm, provider_registry=registry).repair())

    # Cycle 2 (re-seed with same reports; in practice QA would re-run)
    MockRepairProvider.response = _repair_response(2)
    result2 = asyncio.run(RepairAgent(sm, provider_registry=registry).repair())

    assert result2.cycle == 2

    history = sm.load_repair_history()
    assert len(history.cycles) == 2
    assert history.cycles[0].cycle == 1
    assert history.cycles[1].cycle == 2


def test_cycle_archive_files_exist(tmp_path: Path) -> None:
    """Each cycle must produce archived plan and report files."""
    sm = _initialized_state(tmp_path)
    _seed_qa_reports(sm)
    registry = _mock_registry()

    MockRepairProvider.response = _repair_response(1)
    asyncio.run(RepairAgent(sm, provider_registry=registry).repair())

    MockRepairProvider.response = _repair_response(2)
    asyncio.run(RepairAgent(sm, provider_registry=registry).repair())

    assert (sm.repair_dir / "repair_plan.cycle1.json").exists()
    assert (sm.repair_dir / "repair_plan.cycle2.json").exists()
    assert (sm.repair_dir / "repair_report.cycle1.json").exists()
    assert (sm.repair_dir / "repair_report.cycle2.json").exists()


def test_history_never_overwritten(tmp_path: Path) -> None:
    """RepairHistory must never lose previous cycle entries."""
    sm = _initialized_state(tmp_path)
    _seed_qa_reports(sm)
    registry = _mock_registry()

    for i in range(1, 4):
        MockRepairProvider.response = _repair_response(i)
        asyncio.run(RepairAgent(sm, provider_registry=registry).repair())

    history = sm.load_repair_history()
    assert len(history.cycles) == 3
    cycle_numbers = [c.cycle for c in history.cycles]
    assert cycle_numbers == [1, 2, 3]


# ---------------------------------------------------------------------------
# Tests — RepairHistory model helpers
# ---------------------------------------------------------------------------


def test_repair_history_get_next_cycle_empty() -> None:
    """get_next_cycle on empty history returns 1."""
    history = RepairHistory(project_name="X")
    assert history.get_next_cycle() == 1


def test_repair_history_get_next_cycle_increments() -> None:
    """get_next_cycle returns max cycle + 1."""
    history = RepairHistory(project_name="X")
    from omnix_cli.schemas.repair import RepairCycleEntry

    history.cycles.append(
        RepairCycleEntry(
            cycle=3,
            issues_addressed=2,
            artifacts_generated=1,
            quality_score_before=80,
            status="COMPLETE",
        )
    )
    assert history.get_next_cycle() == 4


# ---------------------------------------------------------------------------
# Tests — RepairPlan severity counts
# ---------------------------------------------------------------------------


def test_repair_plan_severity_counts(tmp_path: Path) -> None:
    """RepairPlan.critical/high/medium/low count properties must be correct."""
    sm = _initialized_state(tmp_path)
    _seed_qa_reports(sm)
    MockRepairProvider.response = _repair_response()

    result = asyncio.run(RepairAgent(sm, provider_registry=_mock_registry()).repair())

    plan = result.repair_plan
    assert plan.critical_count == 1
    assert plan.high_count == 1
    assert plan.medium_count == 1
    assert plan.low_count == 1


# ---------------------------------------------------------------------------
# Tests — CLI commands (smoke tests via Typer test runner)
# ---------------------------------------------------------------------------


def test_repair_cli_command(tmp_path: Path) -> None:
    """omnix repair must succeed and produce repair outputs."""
    from typer.testing import CliRunner

    from omnix_cli.cli.main import app

    sm = _initialized_state(tmp_path)
    _seed_qa_reports(sm)
    MockRepairProvider.response = _repair_response()

    # Patch the registry so the CLI uses our mock
    import omnix_cli.agents.repair.agent as repair_module
    original = repair_module.build_default_provider_registry

    def _patched_registry(_: object) -> ProviderRegistry:
        return _mock_registry()

    repair_module.build_default_provider_registry = _patched_registry  # type: ignore[assignment]
    try:
        runner = CliRunner()
        result = runner.invoke(app, ["repair", "--workspace", str(tmp_path)])
        assert result.exit_code == 0, result.output
        assert "Repair Cycle #1 Complete" in result.output
        assert "Issues Processed" in result.output
    finally:
        repair_module.build_default_provider_registry = original  # type: ignore[assignment]


def test_repairs_cli_command(tmp_path: Path) -> None:
    """omnix repairs must display repair history after a repair run."""
    from typer.testing import CliRunner

    from omnix_cli.cli.main import app

    sm = _initialized_state(tmp_path)
    _seed_qa_reports(sm)
    MockRepairProvider.response = _repair_response()

    import omnix_cli.agents.repair.agent as repair_module
    original = repair_module.build_default_provider_registry

    def _patched_registry(_: object) -> ProviderRegistry:
        return _mock_registry()

    repair_module.build_default_provider_registry = _patched_registry  # type: ignore[assignment]
    try:
        runner = CliRunner()
        runner.invoke(app, ["repair", "--workspace", str(tmp_path)])
        result = runner.invoke(app, ["repairs", "--workspace", str(tmp_path)])
        assert result.exit_code == 0, result.output
        assert "Repair History" in result.output
        assert "Total Repair Cycles: 1" in result.output
    finally:
        repair_module.build_default_provider_registry = original  # type: ignore[assignment]


def test_repairs_cli_no_history(tmp_path: Path) -> None:
    """omnix repairs must give a clear error if no repair has been run."""
    from typer.testing import CliRunner

    from omnix_cli.cli.main import app

    _initialized_state(tmp_path)

    runner = CliRunner()
    result = runner.invoke(app, ["repairs", "--workspace", str(tmp_path)])
    assert result.exit_code == 1
    assert "Repair history not found" in result.output


# ---------------------------------------------------------------------------
# Tests — Provider fallback
# ---------------------------------------------------------------------------


def test_repair_agent_falls_back_to_qa_role(tmp_path: Path) -> None:
    """Repair agent should use QA role when REPAIR role is not configured."""
    sm = _initialized_state(tmp_path)
    # Assign to QA role, not REPAIR
    sm.save_models(
        sm.load_models().with_assignment(AgentRole.QA, provider="mock", model="qa-model")
    )
    _seed_qa_reports(sm)
    MockRepairProvider.response = _repair_response()

    result = asyncio.run(RepairAgent(sm, provider_registry=_mock_registry()).repair())
    assert result.cycle == 1


def test_repair_agent_falls_back_to_master_role(tmp_path: Path) -> None:
    """Repair agent should use MASTER role when neither REPAIR nor QA is configured."""
    sm = _initialized_state(tmp_path)
    # Default _initialized_state already has MASTER assigned; no REPAIR or QA
    _seed_qa_reports(sm)
    MockRepairProvider.response = _repair_response()

    result = asyncio.run(RepairAgent(sm, provider_registry=_mock_registry()).repair())
    assert result.cycle == 1
