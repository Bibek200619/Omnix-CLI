from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from aicli.cli.main import app
from aicli.core.settings import Settings
from aicli.core.state_manager import StateManager
from aicli.providers.registry import ProviderRegistry
from aicli.schemas.blueprint import (
    ArchitectureNote,
    EntityDefinition,
    FeatureDefinition,
    ModuleDefinition,
    ProjectBlueprint,
)
from aicli.schemas.tasks import AgentRole
from tests.test_architect_agent import MockArchitectProvider

runner = CliRunner()


def test_blueprint_command_displays_architecture_summary(tmp_path: Path) -> None:
    state_manager = StateManager(tmp_path)
    state_manager.init_project(project_name="CRM")
    state_manager.save_blueprint(
        ProjectBlueprint(
            project_name="CRM",
            description="Customer relationship management workspace.",
            features=[FeatureDefinition(name="Contact Management")],
            entities=[EntityDefinition(name="Contact")],
            modules=[ModuleDefinition(name="Sales Workspace")],
            architecture_notes=[ArchitectureNote(content="Keep structure product-level.")],
        )
    )

    result = runner.invoke(app, ["blueprint", "--workspace", str(tmp_path)])

    assert result.exit_code == 0
    assert "Project Name\nCRM" in result.stdout
    assert "Description\nCustomer relationship management workspace." in result.stdout
    assert "Features\n* Contact Management" in result.stdout
    assert "Entities\n* Contact" in result.stdout
    assert "Modules\n* Sales Workspace" in result.stdout
    assert "Architecture Notes\n* Keep structure product-level." in result.stdout


def test_blueprint_command_can_print_json(tmp_path: Path) -> None:
    state_manager = StateManager(tmp_path)
    state_manager.init_project(project_name="CRM")

    result = runner.invoke(app, ["blueprint", "--workspace", str(tmp_path), "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["project_name"] == "CRM"
    assert payload["features"] == []


def test_architect_command_runs_configured_provider_and_persists_blueprint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_manager = StateManager(tmp_path)
    state_manager.init_project(project_name="CRM")
    state_manager.save_models(
        state_manager.load_models().with_assignment(
            AgentRole.ARCHITECT,
            provider="mock",
            model="architect-model",
        )
    )
    MockArchitectProvider.response = json.dumps(
        {
            "project_name": "CRM",
            "description": "Customer relationship management workspace.",
            "features": [{"name": "Contact Management"}],
            "entities": [{"name": "Contact"}],
            "modules": [{"name": "Sales Workspace"}],
            "architecture_notes": [{"content": "Architecture only, no code."}],
        }
    )
    registry = ProviderRegistry(settings=Settings())
    registry.register("mock", MockArchitectProvider)
    monkeypatch.setattr(
        "aicli.agents.architect.agent.build_default_provider_registry",
        lambda settings: registry,
    )

    result = runner.invoke(app, ["architect", "--workspace", str(tmp_path)])

    assert result.exit_code == 0
    assert "Blueprint updated" in result.stdout
    assert "Features: 1" in result.stdout
    blueprint = state_manager.load_blueprint()
    assert blueprint.features[0].name == "Contact Management"
