"""Phase 0 Master Agent implementation.

The Master Agent is the only user-facing agent. During Phase 0 it records user
intent in project memory but deliberately does not generate code or call models.
"""

from __future__ import annotations

from dataclasses import dataclass

from aicli.memory.memory_manager import MemoryManager
from aicli.schemas.tasks import AgentRole


@dataclass(slots=True)
class MasterAgent:
    """User-facing orchestration boundary."""

    memory_manager: MemoryManager

    async def handle_message(self, message: str) -> str:
        """Record a user message and return the current Phase 0 response."""

        normalized_message = message.strip()
        if not normalized_message:
            msg = "Chat messages cannot be empty."
            raise ValueError(msg)

        response = (
            "Master Agent recorded the goal. Phase 0 supports project setup, "
            "model-role configuration, and persistent memory. Code generation "
            "is gated until provider, planner, integration, and QA phases are implemented."
        )

        self.memory_manager.record_agent_output(
            role=AgentRole.MASTER,
            summary="Recorded user chat message",
            content={
                "user_message": normalized_message,
                "response": response,
                "phase": "0",
            },
        )
        return response
