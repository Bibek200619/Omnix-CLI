from __future__ import annotations

import asyncio
from pathlib import Path

from aicli.agents.master.agent import MasterAgent
from aicli.core.state_manager import StateManager
from aicli.memory.memory_manager import MemoryManager
from aicli.providers.base import BaseProvider
from aicli.providers.registry import ProviderRegistry
from aicli.schemas.tasks import AgentRole


class MockMasterProvider(BaseProvider):
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
        assert system_prompt is not None
        assert "You are the Master Agent of AI-CLI" in system_prompt
        assert "Goals:" in system_prompt
        return f"model response for {prompt}"


def test_master_agent_uses_configured_provider_and_persists_turn(tmp_path: Path) -> None:
    state_manager = StateManager(tmp_path)
    state_manager.init_project(project_name="CRM")
    state_manager.save_models(
        state_manager.load_models().with_assignment(
            AgentRole.MASTER,
            provider="mock",
            model="master-model",
        )
    )
    memory_manager = MemoryManager(state_manager)
    registry = ProviderRegistry()
    registry.register("mock", MockMasterProvider)
    agent = MasterAgent(memory_manager, provider_registry=registry)

    response = asyncio.run(agent.handle_message("Build a CRM platform"))

    memory = memory_manager.load_memory()
    assert response == "model response for Build a CRM platform"
    assert memory.goals[0].title == "Build a CRM platform"
    assert [entry.role.value for entry in memory.conversations] == ["user", "assistant"]
    assert memory.conversations[1].content == response
    assert memory.agent_outputs[0].content["provider"] == "mock"
    assert memory.agent_outputs[0].content["model"] == "master-model"


def test_master_agent_recalls_goal_without_configured_provider(tmp_path: Path) -> None:
    state_manager = StateManager(tmp_path)
    state_manager.init_project(project_name="CRM")

    first_agent = MasterAgent(MemoryManager(state_manager))
    asyncio.run(first_agent.handle_message("Build a CRM platform"))

    second_agent = MasterAgent(MemoryManager(StateManager(tmp_path)))
    response = asyncio.run(second_agent.handle_message("What are we building?"))

    assert "You previously recorded a goal to Build a CRM platform" in response


def test_master_agent_records_decisions_without_provider(tmp_path: Path) -> None:
    state_manager = StateManager(tmp_path)
    state_manager.init_project(project_name="CRM")
    memory_manager = MemoryManager(state_manager)
    agent = MasterAgent(memory_manager)

    response = asyncio.run(agent.handle_message("We will use FastAPI."))

    memory = memory_manager.load_memory()
    assert "Master Agent recorded the decision" in response
    assert memory.decisions[0].title == "Use FastAPI"
