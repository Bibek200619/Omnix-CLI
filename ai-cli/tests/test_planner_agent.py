from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from omnix_cli.agents.planner import PlannerAgent
from omnix_cli.agents.planner.evolution import evolve_task_plan
from omnix_cli.agents.planner.validation import validate_task_plan
from omnix_cli.core.exceptions import TaskValidationError
from omnix_cli.core.state_manager import StateManager
from omnix_cli.memory.memory_manager import MemoryManager
from omnix_cli.providers.base import BaseProvider
from omnix_cli.providers.registry import ProviderRegistry
from omnix_cli.schemas.blueprint import (
    ArchitectureNote,
    EntityDefinition,
    FeatureDefinition,
    ModuleDefinition,
    PageDefinition,
    ProjectBlueprint,
)
from omnix_cli.schemas.tasks import (
    AgentRole,
    TaskAssignedAgent,
    TaskDefinition,
    TaskPlan,
    TaskPriority,
    TaskStatus,
)


class MockPlannerProvider(BaseProvider):
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


def test_planner_agent_generates_and_persists_tasks(tmp_path: Path) -> None:
    state_manager = _initialized_state(tmp_path)
    memory_manager = MemoryManager(state_manager)
    memory_manager.add_goal("Build a CRM platform")
    memory_manager.add_decision("Use FastAPI")
    registry = _mock_registry()
    MockPlannerProvider.response = json.dumps(_crm_task_plan_payload())

    result = asyncio.run(
        PlannerAgent(
            state_manager,
            memory_manager=memory_manager,
            provider_registry=registry,
        ).run()
    )

    task_plan = state_manager.load_tasks()
    memory = memory_manager.load_memory()
    assert result.provider == "mock"
    assert result.model == "planner-model"
    assert result.task_count == 4
    assert result.new_task_count == 4
    assert result.tasks_by_agent == {
        "database": 1,
        "backend": 1,
        "frontend": 1,
        "qa": 1,
    }
    assert [task.id for task in task_plan.tasks] == [
        "task_001",
        "task_002",
        "task_003",
        "task_004",
    ]
    assert task_plan.tasks[1].dependencies == ["task_001"]
    assert task_plan.tasks[2].dependencies == ["task_002"]
    assert "Contact Management" in MockPlannerProvider.last_prompt
    assert "Build a CRM platform" in MockPlannerProvider.last_prompt
    assert "Use FastAPI" in MockPlannerProvider.last_prompt
    assert MockPlannerProvider.last_system_prompt is not None
    assert "You are the Task Planner Agent of Omnix CLI" in MockPlannerProvider.last_system_prompt
    assert memory.agent_outputs[0].role == "planner"
    assert memory.agent_outputs[0].content["phase"] == "4"


def test_planner_agent_refuses_to_persist_invalid_task_plan(tmp_path: Path) -> None:
    state_manager = _initialized_state(tmp_path)
    memory_manager = MemoryManager(state_manager)
    registry = _mock_registry()
    MockPlannerProvider.response = json.dumps(
        {
            "tasks": [
                {
                    "id": "task_001",
                    "title": "Create Contact API",
                    "description": "Plan backend work for contact management.",
                    "assigned_agent": "backend",
                    "priority": "high",
                    "status": "pending",
                    "dependencies": ["task_999"],
                    "blueprint_reference": "contact_management",
                }
            ]
        }
    )

    with pytest.raises(TaskValidationError, match="unknown task id 'task_999'"):
        asyncio.run(
            PlannerAgent(
                state_manager,
                memory_manager=memory_manager,
                provider_registry=registry,
            ).run()
        )

    assert state_manager.load_tasks().tasks == []
    assert memory_manager.load_memory().agent_outputs == []


def test_task_schema_rejects_unsupported_status() -> None:
    with pytest.raises(ValidationError):
        TaskDefinition.model_validate(
            {
                "id": "task_001",
                "title": "Create Contact API",
                "assigned_agent": "backend",
                "priority": "high",
                "status": "failed",
                "dependencies": [],
                "blueprint_reference": "contact_management",
            }
        )


def test_task_validation_rejects_duplicate_ids_and_bad_dependencies() -> None:
    task_plan = TaskPlan(
        tasks=[
            _task("task_001", "Create Contact Schema", TaskAssignedAgent.DATABASE),
            _task(
                "task_001",
                "Create Contact API",
                TaskAssignedAgent.BACKEND,
                dependencies=["task_999"],
            ),
        ]
    )

    with pytest.raises(TaskValidationError) as error:
        validate_task_plan(task_plan)

    message = str(error.value)
    assert "duplicate task id 'task_001'" in message
    assert "depends on unknown task id 'task_999'" in message


def test_task_evolution_preserves_existing_work_and_adds_new_tasks() -> None:
    existing = TaskPlan(
        tasks=[
            _task(
                "task_001",
                "Create Contact Schema",
                TaskAssignedAgent.DATABASE,
                status=TaskStatus.COMPLETED,
            ),
            _task(
                "task_002",
                "Create Contact API",
                TaskAssignedAgent.BACKEND,
                dependencies=["task_001"],
            ),
        ]
    )
    proposed = TaskPlan(
        tasks=[
            _task(
                "task_010",
                "Create Contact Schema",
                TaskAssignedAgent.DATABASE,
                priority=TaskPriority.CRITICAL,
            ),
            _task(
                "task_011",
                "Create Analytics Dashboard",
                TaskAssignedAgent.FRONTEND,
                dependencies=["task_010"],
                blueprint_reference="analytics",
            ),
        ]
    )

    outcome = evolve_task_plan(existing, proposed)

    assert outcome.new_task_count == 1
    assert outcome.updated_task_count == 1
    assert [task.id for task in outcome.task_plan.tasks] == [
        "task_001",
        "task_002",
        "task_011",
    ]
    assert outcome.task_plan.tasks[0].status == TaskStatus.COMPLETED
    assert outcome.task_plan.tasks[0].priority == TaskPriority.CRITICAL
    assert outcome.task_plan.tasks[2].dependencies == ["task_001"]


def test_task_persistence_round_trips_tasks_json(tmp_path: Path) -> None:
    state_manager = StateManager(tmp_path)
    state_manager.init_project(project_name="CRM")
    task_plan = TaskPlan(
        tasks=[
            _task("task_001", "Create Contact Schema", TaskAssignedAgent.DATABASE)
        ]
    )

    state_manager.save_tasks(task_plan)

    assert (tmp_path / ".project" / "tasks.json").is_file()
    assert state_manager.load_tasks() == task_plan


def _initialized_state(tmp_path: Path) -> StateManager:
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
    return state_manager


def _mock_registry() -> ProviderRegistry:
    registry = ProviderRegistry()
    registry.register("mock", MockPlannerProvider)
    return registry


def _crm_blueprint() -> ProjectBlueprint:
    return ProjectBlueprint(
        project_name="CRM",
        description="Customer relationship management workspace.",
        pages=[
            PageDefinition(
                name="Contacts",
                path="/contacts",
                description="Manage customer contacts.",
            )
        ],
        features=[
            FeatureDefinition(
                name="Contact Management",
                description="Capture and manage customer contacts.",
            )
        ],
        entities=[
            EntityDefinition(
                name="Contact",
                description="A person or company relationship.",
            )
        ],
        modules=[
            ModuleDefinition(
                name="Sales Workspace",
                description="Core CRM operating area.",
            )
        ],
        architecture_notes=[
            ArchitectureNote(content="The blueprint describes product structure only.")
        ],
    )


def _crm_task_plan_payload() -> dict[str, object]:
    return {
        "tasks": [
            {
                "id": "task_001",
                "title": "Create Contact Schema",
                "description": "Plan database work for contact records.",
                "assigned_agent": "database",
                "priority": "critical",
                "status": "pending",
                "dependencies": [],
                "blueprint_reference": "contact_management",
            },
            {
                "id": "task_002",
                "title": "Create Contact API",
                "description": "Plan backend work for contact management.",
                "assigned_agent": "backend",
                "priority": "high",
                "status": "pending",
                "dependencies": ["task_001"],
                "blueprint_reference": "contact_management",
            },
            {
                "id": "task_003",
                "title": "Create Contact UI",
                "description": "Plan frontend work for contact management.",
                "assigned_agent": "frontend",
                "priority": "high",
                "status": "pending",
                "dependencies": ["task_002"],
                "blueprint_reference": "contacts_page",
            },
            {
                "id": "task_004",
                "title": "Test Contact Workflow",
                "description": "Plan QA coverage for contact workflows.",
                "assigned_agent": "qa",
                "priority": "medium",
                "status": "pending",
                "dependencies": ["task_003"],
                "blueprint_reference": "contact_management",
            },
        ]
    }


def _task(
    task_id: str,
    title: str,
    assigned_agent: TaskAssignedAgent,
    *,
    priority: TaskPriority = TaskPriority.HIGH,
    status: TaskStatus = TaskStatus.PENDING,
    dependencies: list[str] | None = None,
    blueprint_reference: str = "contact_management",
) -> TaskDefinition:
    return TaskDefinition(
        id=task_id,
        title=title,
        description=f"Plan work for {title}.",
        assigned_agent=assigned_agent,
        priority=priority,
        status=status,
        dependencies=dependencies or [],
        blueprint_reference=blueprint_reference,
    )
