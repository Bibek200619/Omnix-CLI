"""Tests for the integration commands."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from omnix_cli.cli.main import app
from omnix_cli.core.state_manager import StateManager
from omnix_cli.providers.registry import ProviderRegistry
from omnix_cli.schemas.artifacts import Artifact, ArtifactType
from omnix_cli.schemas.tasks import AgentRole
from tests.test_integration_agent import MockIntegrationProvider

runner = CliRunner()


def _setup_integration_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> StateManager:
    state_manager = StateManager(tmp_path)
    state_manager.init_project(project_name="Test")
    
    # Configure master agent
    state_manager.save_models(
        state_manager.load_models().with_assignment(
            AgentRole.MASTER,
            provider="mock",
            model="master-model",
        )
    )
    
    # Create an artifact
    a1 = Artifact(
        id="art_task_001_1",
        task_id="task_001",
        agent=AgentRole.FRONTEND,
        title="UI",
        artifact_type=ArtifactType.FRONTEND_PAGE,
        content="UI Code",
        version=1,
    )
    state_manager.save_artifact(a1)
    
    # Mock registry and provider
    registry = ProviderRegistry()
    registry.register("mock", MockIntegrationProvider)
    from tests.test_integration_agent import MockIntegrationProvider as IP
    IP.response = json.dumps({
        "status": "success",
        "dependencies": [],
        "conflicts": [],
        "coverage": {
            "implemented_pages": 1,
            "implemented_apis": 0,
            "implemented_entities": 0,
            "gaps": []
        },
        "summary": "OK"
    })
    
    from omnix_cli.agents.integration import agent as agent_module
    monkeypatch.setattr(agent_module, "build_default_provider_registry", lambda _: registry)
    
    return state_manager


def test_integrate_command(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _setup_integration_state(tmp_path, monkeypatch)

    result = runner.invoke(app, ["integrate", "-w", str(tmp_path)])
    
    assert result.exit_code == 0
    assert "Integration Successful!" in result.stdout
    assert "Artifacts Processed: 1" in result.stdout
    
    # Check if integration files exist
    assert (tmp_path / ".project" / "integration" / "integrated_package.json").exists()


def test_integration_summary_command(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _setup_integration_state(tmp_path, monkeypatch)
    
    # Run integration first
    runner.invoke(app, ["integrate", "-w", str(tmp_path)])
    
    result = runner.invoke(app, ["integration", "-w", str(tmp_path)])
    
    assert result.exit_code == 0
    assert "Integration Summary: Test" in result.stdout
    assert "Status:             success" in result.stdout
    assert "Artifacts:          1" in result.stdout
