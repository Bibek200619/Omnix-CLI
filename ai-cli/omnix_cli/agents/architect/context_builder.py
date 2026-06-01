"""Structured context construction for the Architect Agent."""

from __future__ import annotations

from dataclasses import dataclass

from omnix_cli.agents.architect.models import ArchitectContext
from omnix_cli.core.state_manager import StateManager
from omnix_cli.memory.memory_manager import MemoryManager
from omnix_cli.schemas.memory import ProjectMemory


@dataclass(slots=True)
class ArchitectContextBuilder:
    """Build structured project context from blueprint and memory state."""

    state_manager: StateManager
    memory_manager: MemoryManager
    recent_conversation_limit: int = 8

    def build_context(self) -> ArchitectContext:
        """Return the context required for architecture blueprint generation."""

        blueprint = self.state_manager.load_blueprint()
        memory = self.memory_manager.load_memory()

        return ArchitectContext(
            goals=[goal.title for goal in memory.goals],
            decisions=self._decision_titles(memory),
            recent_conversations=[
                f"{conversation.role.value}: {conversation.content}"
                for conversation in memory.conversations[-self.recent_conversation_limit :]
            ],
            existing_blueprint=blueprint,
        )

    def _decision_titles(self, memory: ProjectMemory) -> list[str]:
        decision_titles = [decision.title for decision in memory.decisions]
        decision_titles.extend(decision.title for decision in memory.architectural_decisions)
        return decision_titles
