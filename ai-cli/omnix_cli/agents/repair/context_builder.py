"""Context builder for the Repair Agent."""

from __future__ import annotations

from typing import Any

from omnix_cli.core.state_manager import StateManager


class RepairContextBuilder:
    """Assembles all QA reports and project state needed for repair planning."""

    def __init__(self, state_manager: StateManager) -> None:
        self.state_manager = state_manager

    def build_context(self) -> dict[str, Any]:
        """Load QA reports, artifacts, blueprint, and integration state."""

        blueprint = self.state_manager.load_blueprint()
        tasks = self.state_manager.load_tasks()
        artifacts = self.state_manager.list_artifacts()

        context: dict[str, Any] = {
            "project_name": blueprint.project_name,
            "blueprint": blueprint.model_dump(mode="json"),
            "tasks": tasks.model_dump(mode="json"),
            "artifacts": [a.model_dump(mode="json") for a in artifacts],
        }

        # QA reports — required for repair
        quality_report = self.state_manager.load_quality_report()
        qa_summary = self.state_manager.load_qa_summary()
        context["quality_report"] = quality_report.model_dump(mode="json")
        context["qa_summary"] = qa_summary.model_dump(mode="json")

        try:
            cov = self.state_manager.load_coverage_report()
            context["coverage_report"] = cov.model_dump(mode="json")
        except Exception:
            context["coverage_report"] = None

        try:
            gap = self.state_manager.load_gap_report()
            context["gap_report"] = gap.model_dump(mode="json")
        except Exception:
            context["gap_report"] = None

        try:
            risk = self.state_manager.load_risk_report()
            context["risk_report"] = risk.model_dump(mode="json")
        except Exception:
            context["risk_report"] = None

        try:
            pkg = self.state_manager.load_integrated_package()
            context["integrated_package"] = pkg.model_dump(mode="json")
        except Exception:
            context["integrated_package"] = None

        try:
            graph = self.state_manager.load_dependency_graph()
            context["dependency_graph"] = graph.model_dump(mode="json")
        except Exception:
            context["dependency_graph"] = None

        return context
