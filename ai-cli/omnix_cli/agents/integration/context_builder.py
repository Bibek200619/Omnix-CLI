"""Integration Agent context builder."""

from __future__ import annotations

from typing import Any

from omnix_cli.core.state_manager import StateManager


class IntegrationContextBuilder:
    """Builds the context for the Integration Agent."""

    def __init__(self, state_manager: StateManager) -> None:
        self.state_manager = state_manager

    def build_context(self) -> dict[str, Any]:
        """Build the complete project context for integration analysis."""

        blueprint = self.state_manager.load_blueprint()
        tasks = self.state_manager.load_tasks()
        artifacts = self.state_manager.list_artifacts()

        return {
            "project_name": blueprint.project_name,
            "blueprint": blueprint.model_dump(),
            "tasks": [t.model_dump() for t in tasks.tasks],
            "artifacts": [
                {
                    "id": a.id,
                    "task_id": a.task_id,
                    "agent": a.agent,
                    "title": a.title,
                    "artifact_type": a.artifact_type,
                    "content": a.content,
                    "metadata": a.metadata,
                }
                for a in artifacts
            ],
        }
