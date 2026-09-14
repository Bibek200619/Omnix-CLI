"""Context builder for the QA Agent."""

from __future__ import annotations

from typing import Any

from omnix_cli.core.state_manager import StateManager


class QAContextBuilder:
    """Assembles the full project state for QA analysis."""

    def __init__(self, state_manager: StateManager) -> None:
        self.state_manager = state_manager

    def build_context(self) -> dict[str, Any]:
        """Load all relevant project state into a dictionary."""

        blueprint = self.state_manager.load_blueprint()
        tasks = self.state_manager.load_tasks()
        artifacts = self.state_manager.list_artifacts()
        memory = self.state_manager.load_memory()

        context: dict[str, Any] = {
            "project_name": blueprint.project_name,
            "blueprint": blueprint.model_dump(mode="json"),
            "tasks": tasks.model_dump(mode="json"),
            "artifacts": [a.model_dump(mode="json") for a in artifacts],
            "memory": memory.model_dump(mode="json"),
            "goals": [g.model_dump(mode="json") for g in blueprint.goals],
            "decisions": [d.model_dump(mode="json") for d in memory.decisions],
        }

        # Try to load integration outputs
        try:
            package = self.state_manager.load_integrated_package()
            context["integrated_package"] = package.model_dump(mode="json")
        except Exception:
            context["integrated_package"] = None

        try:
            graph = self.state_manager.load_dependency_graph()
            context["dependency_graph"] = graph.model_dump(mode="json")
        except Exception:
            context["dependency_graph"] = None

        try:
            report = self.state_manager.load_integration_report()
            context["integration_report"] = report.model_dump(mode="json")
        except Exception:
            context["integration_report"] = None

        try:
            conflicts = self.state_manager.load_conflict_report()
            context["conflict_report"] = conflicts.model_dump(mode="json")
        except Exception:
            context["conflict_report"] = None

        return context
