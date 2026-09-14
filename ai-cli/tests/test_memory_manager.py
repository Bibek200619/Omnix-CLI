from __future__ import annotations

from pathlib import Path

from omnix_cli.core.state_manager import StateManager
from omnix_cli.memory.memory_manager import MemoryManager
from omnix_cli.schemas.memory import ConversationRole, GoalStatus


def test_memory_manager_persists_conversations_goals_and_decisions(tmp_path: Path) -> None:
    state_manager = StateManager(tmp_path)
    state_manager.init_project(project_name="CRM")
    memory_manager = MemoryManager(state_manager)

    memory_manager.add_conversation(ConversationRole.USER, "Build a CRM")
    goal = memory_manager.add_goal("Build a CRM")
    decision = memory_manager.add_decision("Use FastAPI")

    reloaded = MemoryManager(StateManager(tmp_path)).load_memory()

    assert reloaded.conversations[0].content == "Build a CRM"
    assert reloaded.goals[0].id == goal.id
    assert reloaded.goals[0].status == GoalStatus.ACTIVE
    assert reloaded.decisions[0].id == decision.id


def test_memory_manager_deduplicates_goals_and_decisions(tmp_path: Path) -> None:
    state_manager = StateManager(tmp_path)
    state_manager.init_project(project_name="CRM")
    memory_manager = MemoryManager(state_manager)

    first_goal = memory_manager.add_goal("Build a CRM")
    second_goal = memory_manager.add_goal(" build   a crm ")
    first_decision = memory_manager.add_decision("Use FastAPI")
    second_decision = memory_manager.add_decision("use fastapi")

    memory = memory_manager.load_memory()
    assert first_goal.id == second_goal.id
    assert first_decision.id == second_decision.id
    assert len(memory.goals) == 1
    assert len(memory.decisions) == 1
