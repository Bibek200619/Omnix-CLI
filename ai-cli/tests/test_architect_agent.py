from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from aicli.agents.architect import ArchitectAgent
from aicli.core.exceptions import BlueprintValidationError
from aicli.core.state_manager import StateManager
from aicli.memory.memory_manager import MemoryManager
from aicli.providers.base import BaseProvider
from aicli.providers.registry import ProviderRegistry
from aicli.schemas.blueprint import (
    ArchitectureNote,
    EntityDefinition,
    FeatureDefinition,
    ModuleDefinition,
    ProjectBlueprint,
)
from aicli.schemas.tasks import AgentRole


class MockArchitectProvider(BaseProvider):
    response: str = ""
    last_prompt: str = ""
    last_system_prompt: str | None = None

    @property
    def provider_name(self) -> str:
        return "mock"

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.2,
    ) -> str:
        self._validate_prompt(prompt)
        type(self).last_prompt = prompt
        type(self).last_system_prompt = system_prompt
        return type(self).response


def test_architect_agent_generates_valid_blueprint_from_goals(tmp_path: Path) -> None:
    state_manager = _initialized_state(tmp_path)
    memory_manager = MemoryManager(state_manager)
    memory_manager.add_goal("Build a CRM platform")
    memory_manager.add_decision("Use FastAPI")
    registry = _mock_registry()
    MockArchitectProvider.response = json.dumps(_crm_blueprint_payload())

    result = asyncio.run(
        ArchitectAgent(
            state_manager,
            memory_manager=memory_manager,
            provider_registry=registry,
        ).run()
    )

    blueprint = state_manager.load_blueprint()
    memory = memory_manager.load_memory()
    assert result.provider == "mock"
    assert result.model == "architect-model"
    assert blueprint.project_name == "CRM"
    assert blueprint.goals[0].title == "Build a CRM platform"
    assert blueprint.features[0].name == "Contact Management"
    assert blueprint.entities[0].name == "Contact"
    assert blueprint.modules[0].name == "Sales Workspace"
    assert "Build a CRM platform" in MockArchitectProvider.last_prompt
    assert "Use FastAPI" in MockArchitectProvider.last_prompt
    assert MockArchitectProvider.last_system_prompt is not None
    assert "You are the Architect Agent of AI-CLI" in MockArchitectProvider.last_system_prompt
    assert memory.agent_outputs[0].role == "architect"
    assert memory.agent_outputs[0].content["phase"] == "3"


def test_architect_agent_updates_blueprint_without_replacing_existing_context(
    tmp_path: Path,
) -> None:
    state_manager = _initialized_state(tmp_path)
    state_manager.save_blueprint(
        ProjectBlueprint(
            project_name="CRM",
            description="Customer relationship management",
            features=[
                FeatureDefinition(
                    name="Contact Management",
                    description="Manage customer contacts.",
                )
            ],
            entities=[EntityDefinition(name="Contact")],
            modules=[ModuleDefinition(name="Sales Workspace")],
            architecture_notes=[
                ArchitectureNote(content="The system centers on customer records.")
            ],
        )
    )
    memory_manager = MemoryManager(state_manager)
    memory_manager.add_goal("Add analytics")
    registry = _mock_registry()
    MockArchitectProvider.response = json.dumps(
        _crm_blueprint_payload(
            features=[
                {
                    "name": "Analytics",
                    "description": "Track CRM performance metrics.",
                }
            ],
            entities=[{"name": "Report", "description": "A saved analytics view."}],
            modules=[{"name": "Analytics Workspace"}],
            notes=[{"content": "Analytics summarizes operational CRM activity."}],
        )
    )

    asyncio.run(
        ArchitectAgent(
            state_manager,
            memory_manager=memory_manager,
            provider_registry=registry,
        ).run()
    )

    blueprint = state_manager.load_blueprint()
    assert [feature.name for feature in blueprint.features] == [
        "Contact Management",
        "Analytics",
    ]
    assert [entity.name for entity in blueprint.entities] == ["Contact", "Report"]
    assert [module.name for module in blueprint.modules] == [
        "Sales Workspace",
        "Analytics Workspace",
    ]
    assert blueprint.goals[0].title == "Add analytics"


def test_architect_agent_refuses_to_save_invalid_blueprint(tmp_path: Path) -> None:
    state_manager = _initialized_state(tmp_path)
    memory_manager = MemoryManager(state_manager)
    registry = _mock_registry()
    MockArchitectProvider.response = json.dumps(
        {
            "project_name": "Broken CRM",
            "description": "Missing required architecture sections.",
        }
    )

    with pytest.raises(BlueprintValidationError, match="at least one feature"):
        asyncio.run(
            ArchitectAgent(
                state_manager,
                memory_manager=memory_manager,
                provider_registry=registry,
            ).run()
        )

    blueprint = state_manager.load_blueprint()
    memory = memory_manager.load_memory()
    assert blueprint.project_name == "CRM"
    assert blueprint.features == []
    assert memory.agent_outputs == []


def _initialized_state(tmp_path: Path) -> StateManager:
    state_manager = StateManager(tmp_path)
    state_manager.init_project(project_name="CRM")
    state_manager.save_models(
        state_manager.load_models().with_assignment(
            AgentRole.ARCHITECT,
            provider="mock",
            model="architect-model",
        )
    )
    return state_manager


def _mock_registry() -> ProviderRegistry:
    registry = ProviderRegistry()
    registry.register("mock", MockArchitectProvider)
    return registry


def _crm_blueprint_payload(
    *,
    features: list[dict[str, object]] | None = None,
    entities: list[dict[str, object]] | None = None,
    modules: list[dict[str, object]] | None = None,
    notes: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "project_name": "CRM",
        "description": "Customer relationship management workspace.",
        "pages": [
            {
                "name": "Dashboard",
                "path": "/dashboard",
                "description": "Overview of CRM activity.",
            }
        ],
        "features": features
        or [
            {
                "name": "Contact Management",
                "description": "Capture and manage customer contacts.",
            }
        ],
        "entities": entities
        or [{"name": "Contact", "description": "A person or company relationship."}],
        "modules": modules
        or [{"name": "Sales Workspace", "description": "Core CRM operating area."}],
        "architecture_notes": notes
        or [{"content": "The blueprint describes product structure only."}],
        "assumptions": ["Users need a shared CRM workspace."],
        "constraints": ["No code generation in Phase 3."],
        "future_enhancements": ["Automation rules"],
    }
