"""Frontend Agent context builder."""

from __future__ import annotations

from typing import Any

from omnix_cli.core.state_manager import StateManager
from omnix_cli.memory.memory_manager import MemoryManager


class FrontendContextBuilder:
    """Builds the context for the Frontend Agent."""

    def __init__(
        self,
        state_manager: StateManager,
        memory_manager: MemoryManager | None = None,
    ) -> None:
        self.state_manager = state_manager
        self.memory_manager = memory_manager or MemoryManager(state_manager)

    def build_context(self) -> dict[str, Any]:
        """Build the full context dictionary for the Frontend Agent."""

        blueprint = self.state_manager.load_blueprint()
        memory = self.state_manager.load_memory()
        tasks = self.state_manager.load_tasks()

        return {
            "project_name": blueprint.project_name,
            "project_description": blueprint.description,
            "stack": blueprint.stack,
            "pages": [p.model_dump() for p in blueprint.pages],
            "features": [f.model_dump() for f in blueprint.features],
            "decisions": [d.model_dump() for d in memory.decisions],
            "architectural_decisions": [ad.model_dump() for ad in memory.architectural_decisions],
            "recent_conversations": [
                {"role": c.role, "content": c.content}
                for c in memory.conversations[-5:]
            ],
            "existing_tasks": [t.model_dump() for t in tasks.tasks],
        }
