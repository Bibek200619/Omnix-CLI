"""Tests for QA CLI commands."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from omnix_cli.cli.main import app
from omnix_cli.core.state_manager import StateManager
from omnix_cli.schemas.qa import QAStatus, QASummary

runner = CliRunner()


def test_qa_command_runs_analysis(tmp_path: Path) -> None:
    """Test the 'omnix qa' command."""

    state_manager = StateManager(tmp_path)
    state_manager.init_project(project_name="Test Project")
    
    # Mock the evaluate method of QAAgent
    with patch("omnix_cli.agents.qa.agent.QAAgent.evaluate") as mock_evaluate:
        # Create a mock result
        from omnix_cli.agents.qa.models import QAAgentResult
        from omnix_cli.schemas.qa import CoverageReport, GapReport, QualityReport, RiskReport
        
        summary = QASummary(
            project_name="Test Project",
            version=1,
            quality_score=85,
            coverage_score=90,
            gap_score=95,
            risk_score=80,
            critical_issues=0,
            high_issues=1,
            medium_issues=2,
            low_issues=3,
            status=QAStatus.ACCEPTABLE,
        )
        
        mock_evaluate.return_value = QAAgentResult(
            provider="mock",
            model="mock-model",
            summary=summary,
            quality_report=QualityReport(
                project_name="Test Project", overall_score=85, status=QAStatus.ACCEPTABLE
            ),
            coverage_report=CoverageReport(project_name="Test Project", coverage_score=90),
            gap_report=GapReport(project_name="Test Project", gap_score=95),
            risk_report=RiskReport(project_name="Test Project", risk_score=80),
        )
        
        result = runner.invoke(app, ["qa", "--workspace", str(tmp_path)])
        
        assert result.exit_code == 0
        assert "QA Analysis Complete!" in result.stdout
        assert "Quality Score:    85" in result.stdout
        assert "Status:           ACCEPTABLE" in result.stdout


def test_quality_command_displays_summary(tmp_path: Path) -> None:
    """Test the 'omnix quality' command."""

    state_manager = StateManager(tmp_path)
    state_manager.init_project(project_name="Test Project")
    
    # Save a mock summary and report
    from omnix_cli.schemas.qa import CoverageReport, GapReport, QualityReport, RiskReport
    
    summary = QASummary(
        project_name="Test Project",
        version=1,
        quality_score=92,
        coverage_score=98,
        gap_score=100,
        risk_score=95,
        critical_issues=0,
        high_issues=0,
        medium_issues=1,
        low_issues=2,
        status=QAStatus.PASSED,
    )
    
    quality = QualityReport(
        project_name="Test Project",
        overall_score=92,
        status=QAStatus.PASSED,
        findings=[]
    )
    
    state_manager.save_qa_reports(
        summary=summary,
        quality=quality,
        coverage=CoverageReport(project_name="Test Project"),
        gap=GapReport(project_name="Test Project"),
        risk=RiskReport(project_name="Test Project"),
    )
    
    result = runner.invoke(app, ["quality", "--workspace", str(tmp_path)])
    
    assert result.exit_code == 0
    assert "Quality Summary: Test Project" in result.stdout
    assert "Quality Score:      92" in result.stdout
    assert "Status:             PASSED" in result.stdout
