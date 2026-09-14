"""Tests for the Integration Agent."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from omnix_cli.agents.integration.agent import IntegrationAgent
from omnix_cli.core.state_manager import StateManager
from omnix_cli.providers.base import BaseProvider
from omnix_cli.providers.registry import ProviderRegistry
from omnix_cli.schemas.artifacts import Artifact, ArtifactType
from omnix_cli.schemas.integration import IntegrationStatus
from omnix_cli.schemas.tasks import AgentRole


class MockIntegrationProvider(BaseProvider):
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


def test_integration_agent_assembles_package(tmp_path: Path) -> None:
    state_manager = _initialized_state(tmp_path)
    registry = _mock_registry()
    
    # Create mock artifacts
    a1 = Artifact(
        id="art_task_001_1",
        task_id="task_001",
        agent=AgentRole.FRONTEND,
        title="Dashboard",
        artifact_type=ArtifactType.FRONTEND_PAGE,
        content="Dashboard UI",
        version=1,
    )
    a2 = Artifact(
        id="art_task_002_1",
        task_id="task_002",
        agent=AgentRole.BACKEND,
        title="Auth API",
        artifact_type=ArtifactType.API_DESIGN,
        content="Auth API Code",
        version=1,
    )
    state_manager.save_artifact(a1)
    state_manager.save_artifact(a2)
    
    MockIntegrationProvider.response = json.dumps({
        "status": "success",
        "dependencies": [
            {
                "source_id": "art_task_001_1",
                "target_id": "art_task_002_1",
                "dependency_type": "frontend_to_backend",
                "description": "Dashboard calls Auth API"
            }
        ],
        "conflicts": [],
        "coverage": {
            "implemented_pages": 1,
            "implemented_apis": 1,
            "implemented_entities": 0,
            "gaps": ["Missing User Entity"]
        },
        "summary": "Integration lookin' good."
    })

    result = asyncio.run(
        IntegrationAgent(
            state_manager,
            provider_registry=registry,
        ).integrate()
    )

    # Verify result
    assert result.package.project_name == "Test Project"
    assert result.package.status == IntegrationStatus.SUCCESS
    assert len(result.package.artifacts) == 2
    assert len(result.package.dependencies) == 1
    assert result.package.dependencies[0].source_id == "art_task_001_1"
    assert result.package.coverage.implemented_pages == 1
    assert "Missing User Entity" in result.package.coverage.gaps

    # Verify persistence
    package = state_manager.load_integrated_package()
    assert package.project_name == "Test Project"
    assert len(package.dependencies) == 1
    
    report = state_manager.load_integration_report()
    assert report.artifacts_processed == 2
    assert report.artifacts_by_agent[AgentRole.FRONTEND] == 1


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
    registry.register("mock", MockIntegrationProvider)
    return registry
