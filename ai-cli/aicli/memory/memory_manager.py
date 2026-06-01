"""Persistent project memory operations."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from aicli.core.state_manager import StateManager
from aicli.schemas.memory import AgentOutput
from aicli.schemas.tasks import AgentRole


class MemoryManager:
    """Typed access layer for project memory."""

    def __init__(self, state_manager: StateManager) -> None:
        self.state_manager = state_manager

    def record_agent_output(
        self,
        role: AgentRole,
        summary: str,
        content: Mapping[str, Any],
    ) -> AgentOutput:
        """Append an agent output entry and persist memory."""

        memory = self.state_manager.load_memory()
        output = AgentOutput(role=role, summary=summary, content=dict(content))
        memory.agent_outputs.append(output)
        self.state_manager.save_memory(memory)
        return output
