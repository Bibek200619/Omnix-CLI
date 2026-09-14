"""Structured context construction for the Master Agent."""

from __future__ import annotations

from dataclasses import dataclass

from omnix_cli.core.state_manager import StateManager
from omnix_cli.memory.memory_manager import MemoryManager
from omnix_cli.schemas.blueprint import ProjectBlueprint
from omnix_cli.schemas.memory import ProjectMemory


@dataclass(slots=True)
class MasterContextBuilder:
    """Build structured project context from blueprint and memory state."""

    state_manager: StateManager
    memory_manager: MemoryManager
    recent_conversation_limit: int = 8
    recent_decision_limit: int = 8

    def build_context(self) -> str:
        """Return a stable plain-text context block for the Master Agent."""

        blueprint = self.state_manager.load_blueprint()
        memory = self.memory_manager.load_memory()

        sections = [
            self._format_project_metadata(blueprint, memory),
            self._format_goals(memory),
            self._format_decisions(memory),
            self._format_recent_conversations(memory),
            self._format_known_issues(memory),
            self._format_blueprint_summary(blueprint),
        ]
        return "\n\n".join(sections)

    def _format_project_metadata(
        self,
        blueprint: ProjectBlueprint,
        memory: ProjectMemory,
    ) -> str:
        project_name = blueprint.project_name or memory.project_name or "<unset>"
        description = blueprint.description or "<unset>"
        return f"Project Name:\n{project_name}\n\nDescription:\n{description}"

    def _format_goals(self, memory: ProjectMemory) -> str:
        if not memory.goals:
            return "Goals:\nNone"

        lines = [f"- {goal.title} ({goal.status.value})" for goal in memory.goals]
        return "Goals:\n" + "\n".join(lines)

    def _format_decisions(self, memory: ProjectMemory) -> str:
        decision_titles = [decision.title for decision in memory.decisions]
        decision_titles.extend(decision.title for decision in memory.architectural_decisions)
        if not decision_titles:
            return "Decisions:\nNone"

        recent_titles = decision_titles[-self.recent_decision_limit :]
        return "Decisions:\n" + "\n".join(f"- {title}" for title in recent_titles)

    def _format_recent_conversations(self, memory: ProjectMemory) -> str:
        if not memory.conversations:
            return "Recent Conversations:\nNone"

        recent_conversations = memory.conversations[-self.recent_conversation_limit :]
        lines = [
            f"- {conversation.role.value}: {conversation.content}"
            for conversation in recent_conversations
        ]
        return "Recent Conversations:\n" + "\n".join(lines)

    def _format_known_issues(self, memory: ProjectMemory) -> str:
        if not memory.known_issues:
            return "Known Issues:\nNone"

        lines = [f"- {issue.title}" for issue in memory.known_issues]
        return "Known Issues:\n" + "\n".join(lines)

    def _format_blueprint_summary(self, blueprint: ProjectBlueprint) -> str:
        stack = ", ".join(f"{key}: {value}" for key, value in sorted(blueprint.stack.items()))
        stack_text = stack or "None"
        return (
            "Blueprint Summary:\n"
            f"Stack: {stack_text}\n"
            f"Goals: {len(blueprint.goals)}\n"
            f"Pages: {len(blueprint.pages)}\n"
            f"Features: {len(blueprint.features)}\n"
            f"Entities: {len(blueprint.entities)}\n"
            f"Modules: {len(blueprint.modules)}\n"
            f"Architecture Notes: {len(blueprint.architecture_notes)}\n"
            f"Routes: {len(blueprint.routes)}\n"
            f"Database Objects: {len(blueprint.database)}\n"
            f"APIs: {len(blueprint.apis)}\n"
            f"Generated Files: {len(blueprint.generated_files)}"
        )
