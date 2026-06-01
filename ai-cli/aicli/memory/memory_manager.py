"""Persistent project memory operations."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from aicli.core.state_manager import StateManager
from aicli.schemas.memory import (
    AgentOutput,
    ConversationEntry,
    ConversationRole,
    GoalStatus,
    ProjectDecision,
    ProjectGoal,
    ProjectMemory,
)
from aicli.schemas.tasks import AgentRole


class MemoryManager:
    """Typed access layer for project memory."""

    def __init__(self, state_manager: StateManager) -> None:
        self.state_manager = state_manager

    def load_memory(self) -> ProjectMemory:
        """Load project memory through validated state persistence."""

        return self.state_manager.load_memory()

    def save_memory(self, memory: ProjectMemory) -> None:
        """Persist project memory through validated state persistence."""

        self.state_manager.save_memory(memory)

    def add_conversation(
        self,
        role: ConversationRole,
        content: str,
    ) -> ConversationEntry:
        """Append a conversation message and persist memory."""

        normalized_content = content.strip()
        if not normalized_content:
            msg = "Conversation content cannot be empty."
            raise ValueError(msg)

        memory = self.load_memory()
        entry = ConversationEntry(role=role, content=normalized_content)
        memory.conversations.append(entry)
        self.save_memory(memory)
        return entry

    def add_goal(
        self,
        title: str,
        *,
        status: GoalStatus = GoalStatus.ACTIVE,
    ) -> ProjectGoal:
        """Append a goal unless an equivalent goal already exists."""

        normalized_title = title.strip()
        if not normalized_title:
            msg = "Goal title cannot be empty."
            raise ValueError(msg)

        memory = self.load_memory()
        existing_goal = self._find_goal(memory, normalized_title)
        if existing_goal is not None:
            return existing_goal

        goal = ProjectGoal(
            id=self._next_goal_id(memory),
            title=normalized_title,
            status=status,
        )
        memory.goals.append(goal)
        self.save_memory(memory)
        return goal

    def add_decision(self, title: str, *, rationale: str = "") -> ProjectDecision:
        """Append a project decision unless an equivalent decision already exists."""

        normalized_title = title.strip()
        if not normalized_title:
            msg = "Decision title cannot be empty."
            raise ValueError(msg)

        memory = self.load_memory()
        existing_decision = self._find_decision(memory, normalized_title)
        if existing_decision is not None:
            return existing_decision

        decision = ProjectDecision(
            id=self._next_decision_id(memory),
            title=normalized_title,
            rationale=rationale.strip(),
        )
        memory.decisions.append(decision)
        self.save_memory(memory)
        return decision

    def get_recent_conversations(self, limit: int = 10) -> list[ConversationEntry]:
        """Return recent conversations in chronological order."""

        memory = self.load_memory()
        return memory.conversations[-limit:]

    def get_goals(self, status: GoalStatus | None = None) -> list[ProjectGoal]:
        """Return goals, optionally filtered by status."""

        memory = self.load_memory()
        if status is None:
            return list(memory.goals)
        return [goal for goal in memory.goals if goal.status == status]

    def get_decisions(self, limit: int | None = None) -> list[ProjectDecision]:
        """Return project decisions in chronological order."""

        memory = self.load_memory()
        decisions = list(memory.decisions)
        if limit is None:
            return decisions
        return decisions[-limit:]

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

    def _find_goal(self, memory: ProjectMemory, title: str) -> ProjectGoal | None:
        normalized_title = self._normalize_lookup(title)
        for goal in memory.goals:
            if self._normalize_lookup(goal.title) == normalized_title:
                return goal
        return None

    def _find_decision(self, memory: ProjectMemory, title: str) -> ProjectDecision | None:
        normalized_title = self._normalize_lookup(title)
        for decision in memory.decisions:
            if self._normalize_lookup(decision.title) == normalized_title:
                return decision
        return None

    def _next_goal_id(self, memory: ProjectMemory) -> str:
        return f"goal_{len(memory.goals) + 1:03d}"

    def _next_decision_id(self, memory: ProjectMemory) -> str:
        return f"decision_{len(memory.decisions) + 1:03d}"

    def _normalize_lookup(self, value: str) -> str:
        return " ".join(value.casefold().split())
