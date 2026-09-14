"""Tests for the QA Agent."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from omnix_cli.agents.qa.agent import QAAgent
from omnix_cli.core.state_manager import StateManager
from omnix_cli.providers.base import BaseProvider
from omnix_cli.providers.registry import ProviderRegistry
from omnix_cli.schemas.tasks import AgentRole


class MockQAProvider(BaseProvider):
    """Mock provider for QA testing."""

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


def test_qa_agent_evaluates_project(tmp_path: Path) -> None:
    """Test that the QA Agent can evaluate a project and produce reports."""

    state_manager = _initialized_state(tmp_path)
    registry = _mock_registry()
    
    MockQAProvider.response = json.dumps({
        "quality_report": {
            "overall_score": 91,
            "critical_issues": 0,
            "high_issues": 0,
            "medium_issues": 1,
            "low_issues": 2,
            "findings": [
                {
                    "id": "QA-Q-001",
                    "title": "Minor Typo",
                    "description": "Typo in API docs",
                    "severity": "low",
                    "category": "Architecture",
                    "explanation": "The API documentation has a spelling error."
                }
            ],
            "status": "PASSED",
            "summary": "Excellent work."
        },
        "coverage_report": {
            "coverage_score": 100,
            "missing_pages": [],
            "missing_routes": [],
            "missing_apis": [],
            "missing_entities": [],
            "missing_workflows": [],
            "findings": []
        },
        "gap_report": {
            "gap_score": 100,
            "findings": []
        },
        "risk_report": {
            "risk_score": 95,
            "findings": [
                {
                    "id": "QA-R-001",
                    "title": "Scalability Risk",
                    "description": "Database might need indexing",
                    "severity": "low",
                    "category": "Risk",
                    "explanation": "Large datasets may slow down queries."
                }
            ]
        }
    })

    result = asyncio.run(
        QAAgent(
            state_manager,
            provider_registry=registry,
        ).evaluate()
    )

    # Verify result
    assert result.summary.quality_score == 91
    assert result.summary.status == "PASSED"
    assert len(result.quality_report.findings) == 1
    assert result.summary.version == 1

    # Verify persistence
    summary = state_manager.load_qa_summary()
    assert summary.quality_score == 91
    assert summary.version == 1
    
    quality = state_manager.load_quality_report()
    assert quality.overall_score == 91
    assert len(quality.findings) == 1

    # Verify history
    assert (state_manager.qa_history_dir / "qa_summary.v1.json").exists()
    assert (state_manager.qa_history_dir / "quality_report.v1.json").exists()

    # Run again to check versioning
    result2 = asyncio.run(
        QAAgent(
            state_manager,
            provider_registry=registry,
        ).evaluate()
    )
    assert result2.summary.version == 2
    assert (state_manager.qa_history_dir / "qa_summary.v2.json").exists()


def _initialized_state(tmp_path: Path) -> StateManager:
    state_manager = StateManager(tmp_path)
    state_manager.init_project(project_name="Test Project")
    state_manager.save_models(
        state_manager.load_models().with_assignment(
            AgentRole.MASTER,
            provider="mock",
            model="master-model",
        )
    )
    return state_manager


def _mock_registry() -> ProviderRegistry:
    registry = ProviderRegistry()
    registry.register("mock", MockQAProvider)
    return registry
