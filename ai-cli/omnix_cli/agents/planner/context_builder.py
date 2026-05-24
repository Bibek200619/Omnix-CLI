"""Structured context construction for the Planner Agent."""

from __future__ import annotations

from dataclasses import dataclass

from omnix_cli.agents.planner.models import PlannerContext
from omnix_cli.core.state_manager import StateManager
from omnix_cli.memory.memory_manager import MemoryManager
from omnix_cli.schemas.memory import ProjectMemory


@dataclass(slots=True)
class PlannerContextBuilder:
    """Build structured project context from blueprint, memory, and task state."""

    state_manager: StateManager
    memory_manager: MemoryManager
    recent_conversation_limit: int = 8

    def build_context(self) -> PlannerContext:
        """Return the context required for task planning."""

        blueprint = self.state_manager.load_blueprint()
        memory = self.memory_manager.load_memory()
        task_plan = self.state_manager.load_tasks()

        return PlannerContext(
            goals=[goal.title for goal in memory.goals],
            decisions=self._decision_titles(memory),
            recent_conversations=[
                f"{conversation.role.value}: {conversation.content}"
                for conversation in memory.conversations[-self.recent_conversation_limit :]
            ],
            blueprint=blueprint,
            existing_task_plan=task_plan,
        )

    def _decision_titles(self, memory: ProjectMemory) -> list[str]:
        decision_titles = [decision.title for decision in memory.decisions]
        decision_titles.extend(decision.title for decision in memory.architectural_decisions)
        return decision_titles
