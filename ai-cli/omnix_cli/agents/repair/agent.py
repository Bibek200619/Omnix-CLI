"""Repair Agent implementation."""

from __future__ import annotations

import json
from json import JSONDecodeError
from typing import Any, cast

from omnix_cli.agents.repair.context_builder import RepairContextBuilder
from omnix_cli.agents.repair.models import RepairAgentResult
from omnix_cli.agents.repair.prompts import (
    build_repair_system_prompt,
    build_repair_user_prompt,
)
from omnix_cli.core.settings import Settings
from omnix_cli.core.state_manager import StateManager
from omnix_cli.providers.base import BaseProvider
from omnix_cli.providers.exceptions import ProviderConfigurationError, ProviderRequestError
from omnix_cli.providers.registry import ProviderRegistry, build_default_provider_registry
from omnix_cli.schemas.repair import (
    RepairArtifact,
    RepairCycleEntry,
    RepairHistory,
    RepairPlan,
    RepairPlanItem,
    RepairReport,
    RepairSeverity,
    RepairStatus,
)
from omnix_cli.schemas.tasks import AgentRole

# Priority order for sorting repair items
_SEVERITY_ORDER: dict[str, int] = {
    RepairSeverity.CRITICAL: 0,
    RepairSeverity.HIGH: 1,
    RepairSeverity.MEDIUM: 2,
    RepairSeverity.LOW: 3,
}


class RepairAgent:
    """Reads QA findings and generates prioritized repair plans and artifacts."""

    def __init__(
        self,
        state_manager: StateManager,
        *,
        context_builder: RepairContextBuilder | None = None,
        provider_registry: ProviderRegistry | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.state_manager = state_manager
        self.context_builder = context_builder or RepairContextBuilder(state_manager)
        self.provider_registry = provider_registry
        self.settings = settings or Settings()

    async def repair(self) -> RepairAgentResult:
        """Analyze QA findings and produce a repair plan, artifacts, and report."""

        # 1. Determine current cycle number
        history = self._load_or_init_history()
        cycle = history.get_next_cycle()

        # 2. Capture quality score before repair (for history)
        qa_summary = self.state_manager.load_qa_summary()
        quality_score_before = qa_summary.quality_score

        # 3. Build context and call provider
        context = self.context_builder.build_context()
        provider = self._create_provider()

        response = await provider.generate(
            build_repair_user_prompt(context, cycle),
            system_prompt=build_repair_system_prompt(),
            temperature=0.1,
        )

        raw = self._parse_response(response)
        project_name = context.get("project_name", "Unknown")

        # 4. Build RepairPlan — sort items by severity priority
        raw_items: list[dict[str, Any]] = (
            raw.get("repair_plan", {}).get("items", [])
        )
        plan_items = [
            RepairPlanItem(
                id=item.get("id", f"repair_{i+1:03d}"),
                severity=RepairSeverity(item.get("severity", RepairSeverity.LOW)),
                issue=item.get("issue", ""),
                strategy=item.get("strategy", ""),
                target_agent=item.get("target_agent", "backend"),
                qa_finding_id=item.get("qa_finding_id", ""),
                status=RepairStatus(item.get("status", RepairStatus.PLANNED)),
            )
            for i, item in enumerate(raw_items)
        ]
        plan_items.sort(key=lambda p: _SEVERITY_ORDER.get(p.severity, 99))

        plan = RepairPlan(
            project_name=project_name,
            cycle=cycle,
            items=plan_items,
        )

        # 5. Build RepairArtifacts
        raw_artifacts: list[dict[str, Any]] = raw.get("repair_artifacts", [])
        repair_artifacts = [
            RepairArtifact(
                id=art.get("id", f"repair_artifact_{i+1:03d}"),
                repair_plan_id=art.get("repair_plan_id", ""),
                qa_finding_id=art.get("qa_finding_id", ""),
                target_agent=art.get("target_agent", "backend"),
                title=art.get("title", "Repair Artifact"),
                description=art.get("description", ""),
                content=art.get("content", ""),
                cycle=cycle,
                version=1,
            )
            for i, art in enumerate(raw_artifacts)
        ]

        # 6. Build RepairReport
        raw_report: dict[str, Any] = raw.get("repair_report", {})
        report = RepairReport(
            project_name=project_name,
            cycle=cycle,
            issues_processed=len(plan_items),
            critical_count=plan.critical_count,
            high_count=plan.high_count,
            medium_count=plan.medium_count,
            low_count=plan.low_count,
            artifacts_generated=len(repair_artifacts),
            plan_item_ids=[p.id for p in plan_items],
            repair_artifact_ids=[a.id for a in repair_artifacts],
            expected_impact=raw_report.get("expected_impact", ""),
            status="COMPLETE",
        )

        # 7. Persist all outputs
        self.state_manager.save_repair_plan(plan)
        for artifact in repair_artifacts:
            self.state_manager.save_repair_artifact(artifact)
        self.state_manager.save_repair_report(report)

        # 8. Append to history (never overwrites previous entries)
        entry = RepairCycleEntry(
            cycle=cycle,
            issues_addressed=len(plan_items),
            artifacts_generated=len(repair_artifacts),
            quality_score_before=quality_score_before,
            status="COMPLETE",
        )
        history.cycles.append(entry)
        self.state_manager.save_repair_history(history)

        return RepairAgentResult(
            provider=provider.provider_name,
            model=provider.model,
            cycle=cycle,
            repair_plan=plan,
            repair_artifacts=repair_artifacts,
            repair_report=report,
        )

    def _load_or_init_history(self) -> RepairHistory:
        """Load repair history or create a fresh one."""
        try:
            return self.state_manager.load_repair_history()
        except Exception:
            blueprint = self.state_manager.load_blueprint()
            return RepairHistory(project_name=blueprint.project_name)

    def _create_provider(self) -> BaseProvider:
        """Create the provider — prefers REPAIR role, falls back to QA then MASTER."""

        models = self.state_manager.load_models()

        for role in (AgentRole.REPAIR, AgentRole.QA, AgentRole.MASTER):
            assignment = models.assignment_for(role)
            if assignment and assignment.provider and assignment.model:
                break
        else:
            msg = "Repair Agent requires REPAIR, QA, or Master agent configuration."
            raise ProviderConfigurationError(msg)

        registry = self.provider_registry or build_default_provider_registry(self.settings)
        return registry.create(assignment.provider, model=assignment.model)

    def _parse_response(self, response: str) -> dict[str, Any]:
        """Parse the JSON response from the provider."""

        normalized = response.strip()
        if not normalized:
            msg = "Repair provider returned an empty response."
            raise ProviderRequestError(msg)

        try:
            payload = json.loads(normalized)
        except JSONDecodeError:
            payload = self._extract_fenced_json(normalized)

        if not isinstance(payload, dict):
            msg = "Repair provider response must be a JSON object."
            raise ProviderRequestError(msg)

        return cast(dict[str, Any], payload)

    def _extract_fenced_json(self, response: str) -> Any:
        """Extract JSON from markdown fences or bare braces."""

        lines = response.splitlines()
        start_idx = -1
        for i, line in enumerate(lines):
            if line.strip().startswith("```"):
                start_idx = i
                break

        if start_idx == -1:
            first_brace = response.find("{")
            last_brace = response.rfind("}")
            if first_brace != -1 and last_brace != -1:
                try:
                    return json.loads(response[first_brace : last_brace + 1])
                except JSONDecodeError:
                    pass
            msg = "Repair provider returned non-JSON output."
            raise ProviderRequestError(msg)

        end_idx = -1
        for i in range(start_idx + 1, len(lines)):
            if lines[i].strip().startswith("```"):
                end_idx = i
                break

        if end_idx == -1:
            msg = "Repair provider returned malformed fenced JSON."
            raise ProviderRequestError(msg)

        fenced = "\n".join(lines[start_idx + 1 : end_idx]).strip()
        try:
            return json.loads(fenced)
        except JSONDecodeError as exc:
            msg = "Repair provider returned invalid JSON within fences."
            raise ProviderRequestError(msg) from exc
