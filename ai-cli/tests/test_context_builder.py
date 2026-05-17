from __future__ import annotations

from pathlib import Path

from aicli.agents.master.context_builder import MasterContextBuilder
from aicli.core.state_manager import StateManager
from aicli.memory.memory_manager import MemoryManager
from aicli.schemas.memory import ConversationRole


def test_context_builder_includes_blueprint_and_memory(tmp_path: Path) -> None:
    state_manager = StateManager(tmp_path)
    state_manager.init_project(project_name="CRM", description="SaaS CRM")
    memory_manager = MemoryManager(state_manager)
    memory_manager.add_goal("Build SaaS CRM")
    memory_manager.add_decision("Use FastAPI")
    memory_manager.add_conversation(ConversationRole.USER, "Build a CRM")

    context = MasterContextBuilder(state_manager, memory_manager).build_context()

    assert "Project Name:\nCRM" in context
    assert "Description:\nSaaS CRM" in context
    assert "- Build SaaS CRM (active)" in context
    assert "- Use FastAPI" in context
    assert "- user: Build a CRM" in context
    assert "Known Issues:\nNone" in context
