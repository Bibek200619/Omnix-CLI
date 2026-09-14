"""Routing Agent context builder."""

from __future__ import annotations

from typing import Any

from omnix_cli.core.state_manager import StateManager
from omnix_cli.memory.memory_manager import MemoryManager


class RoutingContextBuilder:
    """Builds the context for the Routing Agent."""

    def __init__(
        self,
        state_manager: StateManager,
        memory_manager: MemoryManager | None = None,
    ) -> None:
        self.state_manager = state_manager
        self.memory_manager = memory_manager or MemoryManager(state_manager)

    def build_context(self) -> dict[str, Any]:
        """Build the focused context dictionary for the Routing Agent."""

        blueprint = self.state_manager.load_blueprint()
        memory = self.state_manager.load_memory()
        tasks = self.state_manager.load_tasks()

        # Focus on pages, navigation, and workflows
        return {
            "project_name": blueprint.project_name,
            "project_description": blueprint.description,
            "pages": [p.model_dump() for p in blueprint.pages],
            "features": [f.model_dump() for f in blueprint.features],
            "modules": [m.model_dump() for m in blueprint.modules],
            "apis": [a.model_dump() for a in blueprint.apis],
            "decisions": [d.model_dump() for d in memory.decisions],
            "architectural_decisions": [ad.model_dump() for ad in memory.architectural_decisions],
            "goals": [g.model_dump() for g in memory.goals],
            "existing_routing_tasks": [
                t.model_dump() for t in tasks.tasks 
                if t.assigned_agent.value == "routing"
            ],
        }
