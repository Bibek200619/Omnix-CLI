"""Tests for the `omnix execute` command."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from omnix_cli.cli.main import app
from omnix_cli.core.state_manager import StateManager
from omnix_cli.providers.registry import ProviderRegistry
from omnix_cli.schemas.tasks import (
    AgentRole,
    TaskAssignedAgent,
    TaskDefinition,
    TaskPlan,
    TaskPriority,
    TaskStatus,
)
from tests.test_backend_agent import MockBackendProvider
from tests.test_frontend_agent import MockFrontendProvider

runner = CliRunner()


def test_execute_frontend_task(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state_manager = StateManager(tmp_path)
    state_manager.init_project(project_name="Test")
    
    # Configure frontend agent
    state_manager.save_models(
        state_manager.load_models().with_assignment(
            AgentRole.FRONTEND,
            provider="mock",
            model="frontend-model",
        )
    )
    
    # Create a frontend task
    task = TaskDefinition(
        id="task_001",
        title="Create Login UI",
        description="Login form with validation.",
        assigned_agent=TaskAssignedAgent.FRONTEND,
        priority=TaskPriority.HIGH,
        status=TaskStatus.READY,
        blueprint_reference="auth",
    )
    state_manager.save_tasks(TaskPlan(tasks=[task]))
    
    # Mock registry and provider
    registry = ProviderRegistry()
    registry.register("mock", MockFrontendProvider)
    MockFrontendProvider.response = json.dumps({
        "title": "Login UI",
        "content": "Login form code"
    })
    
    from omnix_cli.agents.frontend import agent as agent_module
    monkeypatch.setattr(agent_module, "build_default_provider_registry", lambda _: registry)

    result = runner.invoke(app, ["execute", "task_001", "-w", str(tmp_path)])
    
    assert result.exit_code == 0, f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    assert "Executing task 'Create Login UI' (task_001) using Frontend Agent..." in result.stdout
    assert "Artifact Generated Successfully!" in result.stdout
    assert "Artifact ID:   art_task_001_1" in result.stdout
    
    # Check if artifact exists
    artifacts = state_manager.list_artifacts()
    assert len(artifacts) == 1
    assert artifacts[0].task_id == "task_001"


def test_execute_backend_task(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state_manager = StateManager(tmp_path)
    state_manager.init_project(project_name="Test")
    
    # Configure backend agent
    state_manager.save_models(
        state_manager.load_models().with_assignment(
            AgentRole.BACKEND,
            provider="mock",
            model="backend-model",
        )
    )
    
    # Create a backend task
    task = TaskDefinition(
        id="task_002",
        title="Create Auth API",
        description="Auth service logic.",
        assigned_agent=TaskAssignedAgent.BACKEND,
        priority=TaskPriority.HIGH,
        status=TaskStatus.READY,
        blueprint_reference="auth",
    )
    state_manager.save_tasks(TaskPlan(tasks=[task]))
    
    # Mock registry and provider
    registry = ProviderRegistry()
    registry.register("mock", MockBackendProvider)
    from tests.test_backend_agent import MockBackendProvider as BP
    BP.response = json.dumps({
        "title": "Auth Service",
        "content": "Auth service code"
    })
    
    from omnix_cli.agents.backend import agent as agent_module
    monkeypatch.setattr(agent_module, "build_default_provider_registry", lambda _: registry)

    result = runner.invoke(app, ["execute", "task_002", "-w", str(tmp_path)])
    
    assert result.exit_code == 0, f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    assert "Executing task 'Create Auth API' (task_002) using Backend Agent..." in result.stdout
    assert "Artifact Generated Successfully!" in result.stdout
    assert "Artifact ID:   art_task_002_1" in result.stdout
    
    # Check if artifact exists
    artifacts = state_manager.list_artifacts()
    assert len(artifacts) == 1
    assert artifacts[0].task_id == "task_002"


def test_execute_task_not_found(tmp_path: Path) -> None:
    state_manager = StateManager(tmp_path)
    state_manager.init_project(project_name="Test")
    
    result = runner.invoke(app, ["execute", "missing", "-w", str(tmp_path)])
    assert result.exit_code == 1
    assert "Task 'missing' not found." in result.stderr


def test_execute_unsupported_agent(tmp_path: Path) -> None:
    state_manager = StateManager(tmp_path)
    state_manager.init_project(project_name="Test")
    
    task = TaskDefinition(
        id="task_001",
        title="DB Task",
        assigned_agent=TaskAssignedAgent.DATABASE,
        blueprint_reference="db",
    )
    state_manager.save_tasks(TaskPlan(tasks=[task]))
    
    result = runner.invoke(app, ["execute", "task_001", "-w", str(tmp_path)])
    assert result.exit_code == 0, f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    assert "Agent 'database' is not yet supported" in result.stderr
