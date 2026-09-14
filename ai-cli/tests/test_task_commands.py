from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from omnix_cli.cli.main import app
from omnix_cli.core.settings import Settings
from omnix_cli.core.state_manager import StateManager
from omnix_cli.providers.registry import ProviderRegistry
from omnix_cli.schemas.tasks import AgentRole, TaskAssignedAgent, TaskPlan
from tests.test_planner_agent import (
    MockPlannerProvider,
    _crm_blueprint,
    _crm_task_plan_payload,
    _task,
)

runner = CliRunner()


def test_plan_command_runs_configured_provider_and_persists_tasks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_manager = StateManager(tmp_path)
    state_manager.init_project(project_name="CRM")
    state_manager.save_blueprint(_crm_blueprint())
    state_manager.save_models(
        state_manager.load_models().with_assignment(
            AgentRole.PLANNER,
            provider="mock",
            model="planner-model",
        )
    )
    MockPlannerProvider.response = json.dumps(_crm_task_plan_payload())
    registry = ProviderRegistry(settings=Settings())
    registry.register("mock", MockPlannerProvider)
    monkeypatch.setattr(
        "omnix_cli.agents.planner.agent.build_default_provider_registry",
        lambda settings: registry,
    )

    result = runner.invoke(app, ["plan", "--workspace", str(tmp_path)])

    assert result.exit_code == 0
    assert "Tasks Generated: 4" in result.stdout
    assert "Database: 1" in result.stdout
    assert "Backend: 1" in result.stdout
    task_plan = state_manager.load_tasks()
    assert len(task_plan.tasks) == 4


def test_tasks_command_displays_persisted_task_plan(tmp_path: Path) -> None:
    state_manager = StateManager(tmp_path)
    state_manager.init_project(project_name="CRM")
    state_manager.save_tasks(
        TaskPlan(
            tasks=[
                _task("task_001", "Create Contact Schema", TaskAssignedAgent.DATABASE),
                _task(
                    "task_002",
                    "Create Contact API",
                    TaskAssignedAgent.BACKEND,
                    dependencies=["task_001"],
                ),
            ]
        )
    )

    result = runner.invoke(app, ["tasks", "--workspace", str(tmp_path)])

    assert result.exit_code == 0
    assert "[HIGH] [PENDING] Create Contact Schema" in result.stdout
    assert "Agent: database" in result.stdout
    assert "[HIGH] [PENDING] Create Contact API" in result.stdout
    assert "Depends On: Create Contact Schema" in result.stdout


def test_tasks_command_can_print_json(tmp_path: Path) -> None:
    state_manager = StateManager(tmp_path)
    state_manager.init_project(project_name="CRM")
    state_manager.save_tasks(
        TaskPlan(
            tasks=[
                _task("task_001", "Create Contact Schema", TaskAssignedAgent.DATABASE)
            ]
        )
    )

    result = runner.invoke(app, ["tasks", "--workspace", str(tmp_path), "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["tasks"][0]["id"] == "task_001"
    assert payload["tasks"][0]["assigned_agent"] == "database"
