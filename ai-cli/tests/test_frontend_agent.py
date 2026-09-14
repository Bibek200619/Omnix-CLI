"""Tests for the Frontend Agent."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from omnix_cli.agents.frontend.agent import FrontendAgent
from omnix_cli.core.state_manager import StateManager
from omnix_cli.memory.memory_manager import MemoryManager
from omnix_cli.providers.base import BaseProvider
from omnix_cli.providers.registry import ProviderRegistry
from omnix_cli.schemas.artifacts import ArtifactType
from omnix_cli.schemas.tasks import (
    AgentRole,
    TaskAssignedAgent,
    TaskDefinition,
    TaskPriority,
    TaskStatus,
)


class MockFrontendProvider(BaseProvider):
    response: str = ""
    last_prompt: str = ""

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
        return type(self).response


def test_frontend_agent_generates_and_persists_artifact(tmp_path: Path) -> None:
    state_manager = _initialized_state(tmp_path)
    memory_manager = MemoryManager(state_manager)
    registry = _mock_registry()
    
    task = _task("task_001", "Create Dashboard UI", TaskAssignedAgent.FRONTEND)
    
    MockFrontendProvider.response = json.dumps({
        "title": "Dashboard UI Component",
        "description": "A responsive dashboard layout with sidebar and main content.",
        "artifact_type": "frontend_component",
        "content": "export const Dashboard = () => <div>Dashboard</div>;",
        "metadata": {"framework": "React"}
    })

    result = asyncio.run(
        FrontendAgent(
            state_manager,
            memory_manager=memory_manager,
            provider_registry=registry,
        ).execute_task(task)
    )

    # Verify result
    assert result.provider == "mock"
    assert result.task_id == "task_001"
    assert result.artifact.title == "Dashboard UI Component"
    assert result.artifact.artifact_type == ArtifactType.FRONTEND_COMPONENT
    assert "export const Dashboard" in result.artifact.content
    assert result.artifact.version == 1
    assert result.artifact.id == "art_task_001_1"

    # Verify persistence
    artifacts = state_manager.list_artifacts()
    assert len(artifacts) == 1
    assert artifacts[0].id == "art_task_001_1"
    
    # Verify memory
    memory = memory_manager.load_memory()
    assert len(memory.agent_outputs) == 1
    assert memory.agent_outputs[0].role == AgentRole.FRONTEND
    assert memory.agent_outputs[0].content["artifact_id"] == "art_task_001_1"


def test_frontend_agent_supports_versioning(tmp_path: Path) -> None:
    state_manager = _initialized_state(tmp_path)
    registry = _mock_registry()
    task = _task("task_001", "Create Dashboard UI", TaskAssignedAgent.FRONTEND)
    
    # First execution
    MockFrontendProvider.response = json.dumps({
        "title": "Dashboard v1",
        "content": "v1 content"
    })
    asyncio.run(FrontendAgent(state_manager, provider_registry=registry).execute_task(task))
    
    # Second execution
    MockFrontendProvider.response = json.dumps({
        "title": "Dashboard v2",
        "content": "v2 content"
    })
    asyncio.run(FrontendAgent(state_manager, provider_registry=registry).execute_task(task))
    
    artifacts = state_manager.list_artifacts()
    assert len(artifacts) == 2
    # list_artifacts sorts by generated_at reverse, so v2 should be first
    assert artifacts[0].version == 2
    assert artifacts[1].version == 1
    assert artifacts[0].id == "art_task_001_2"
    assert artifacts[1].id == "art_task_001_1"


def test_frontend_agent_rejects_wrong_agent_task(tmp_path: Path) -> None:
    state_manager = _initialized_state(tmp_path)
    task = _task("task_001", "Create DB Schema", TaskAssignedAgent.DATABASE)
    
    agent = FrontendAgent(state_manager)
    with pytest.raises(ValueError, match="not assigned to the Frontend Agent"):
        asyncio.run(agent.execute_task(task))


def _initialized_state(tmp_path: Path) -> StateManager:
    state_manager = StateManager(tmp_path)
    state_manager.init_project(project_name="Test Project")
    state_manager.save_models(
        state_manager.load_models().with_assignment(
            AgentRole.FRONTEND,
            provider="mock",
            model="frontend-model",
        )
    )
    return state_manager


def _mock_registry() -> ProviderRegistry:
    registry = ProviderRegistry()
    registry.register("mock", MockFrontendProvider)
    return registry


def _task(
    task_id: str,
    title: str,
    assigned_agent: TaskAssignedAgent,
) -> TaskDefinition:
    return TaskDefinition(
        id=task_id,
        title=title,
        description=f"Work for {title}.",
        assigned_agent=assigned_agent,
        priority=TaskPriority.HIGH,
        status=TaskStatus.PENDING,
        dependencies=[],
        blueprint_reference="ref",
    )
