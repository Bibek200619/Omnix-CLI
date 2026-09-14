"""Tests for the Database Agent."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from omnix_cli.agents.database.agent import DatabaseAgent
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


class MockDatabaseProvider(BaseProvider):
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


def test_database_agent_generates_and_persists_artifact(tmp_path: Path) -> None:
    state_manager = _initialized_state(tmp_path)
    memory_manager = MemoryManager(state_manager)
    registry = _mock_registry()
    
    task = _task("task_db_001", "Design User Schema", TaskAssignedAgent.DATABASE)
    
    MockDatabaseProvider.response = json.dumps({
        "title": "User Schema Design",
        "description": "SQL schema for user management.",
        "artifact_type": "schema_design",
        "content": "CREATE TABLE users (...);",
        "metadata": {"engine": "PostgreSQL"}
    })

    result = asyncio.run(
        DatabaseAgent(
            state_manager,
            memory_manager=memory_manager,
            provider_registry=registry,
        ).execute_task(task)
    )

    # Verify result
    assert result.provider == "mock"
    assert result.task_id == "task_db_001"
    assert result.artifact.title == "User Schema Design"
    assert result.artifact.artifact_type == ArtifactType.SCHEMA_DESIGN
    assert "CREATE TABLE users" in result.artifact.content
    assert result.artifact.version == 1
    assert result.artifact.id == "art_task_db_001_1"

    # Verify persistence
    artifacts = state_manager.list_artifacts()
    assert len(artifacts) == 1
    assert artifacts[0].id == "art_task_db_001_1"
    
    # Verify memory
    memory = memory_manager.load_memory()
    assert len(memory.agent_outputs) == 1
    assert memory.agent_outputs[0].role == AgentRole.DATABASE
    assert memory.agent_outputs[0].content["artifact_id"] == "art_task_db_001_1"


def test_database_agent_supports_versioning(tmp_path: Path) -> None:
    state_manager = _initialized_state(tmp_path)
    registry = _mock_registry()
    task = _task("task_db_001", "Design User Schema", TaskAssignedAgent.DATABASE)
    
    # First execution
    MockDatabaseProvider.response = json.dumps({
        "title": "User v1",
        "content": "v1 content"
    })
    asyncio.run(DatabaseAgent(state_manager, provider_registry=registry).execute_task(task))
    
    # Second execution
    MockDatabaseProvider.response = json.dumps({
        "title": "User v2",
        "content": "v2 content"
    })
    asyncio.run(DatabaseAgent(state_manager, provider_registry=registry).execute_task(task))
    
    artifacts = state_manager.list_artifacts()
    assert len(artifacts) == 2
    assert artifacts[0].version == 2
    assert artifacts[1].version == 1


def test_database_agent_rejects_wrong_agent_task(tmp_path: Path) -> None:
    state_manager = _initialized_state(tmp_path)
    task = _task("task_001", "Create UI", TaskAssignedAgent.FRONTEND)
    
    agent = DatabaseAgent(state_manager)
    with pytest.raises(ValueError, match="not assigned to the Database Agent"):
        asyncio.run(agent.execute_task(task))


def _initialized_state(tmp_path: Path) -> StateManager:
    state_manager = StateManager(tmp_path)
    state_manager.init_project(project_name="Test Project")
    state_manager.save_models(
        state_manager.load_models().with_assignment(
            AgentRole.DATABASE,
            provider="mock",
            model="db-model",
        )
    )
    return state_manager


def _mock_registry() -> ProviderRegistry:
    registry = ProviderRegistry()
    registry.register("mock", MockDatabaseProvider)
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
