"""QA Agent implementation."""

from __future__ import annotations

import json
from json import JSONDecodeError
from typing import Any, cast

from omnix_cli.agents.qa.context_builder import QAContextBuilder
from omnix_cli.agents.qa.models import QAAgentResult
from omnix_cli.agents.qa.prompts import (
    build_qa_system_prompt,
    build_qa_user_prompt,
)
from omnix_cli.core.settings import Settings
from omnix_cli.core.state_manager import StateManager
from omnix_cli.providers.base import BaseProvider
from omnix_cli.providers.exceptions import ProviderConfigurationError, ProviderRequestError
from omnix_cli.providers.registry import ProviderRegistry, build_default_provider_registry
from omnix_cli.schemas.qa import (
    CoverageReport,
    GapReport,
    QASummary,
    QualityReport,
    RiskReport,
)
from omnix_cli.schemas.tasks import AgentRole


class QAAgent:
    """Orchestration agent that evaluates project quality and generates reports."""

    def __init__(
        self,
        state_manager: StateManager,
        *,
        context_builder: QAContextBuilder | None = None,
        provider_registry: ProviderRegistry | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.state_manager = state_manager
        self.context_builder = context_builder or QAContextBuilder(state_manager)
        self.provider_registry = provider_registry
        self.settings = settings or Settings()

    async def evaluate(self) -> QAAgentResult:
        """Analyze project state and produce QA reports."""

        context = self.context_builder.build_context()
        provider = self._create_provider()
        
        response = await provider.generate(
            build_qa_user_prompt(context),
            system_prompt=build_qa_system_prompt(),
            temperature=0.1,
        )
        
        analysis = self._parse_qa_response(response)
        version = self.state_manager.get_next_qa_version()
        project_name = context.get("project_name", "Unknown")

        # 1. Build Reports from Analysis
        quality_report = QualityReport(
            project_name=project_name,
            version=version,
            **analysis.get("quality_report", {})
        )

        coverage_report = CoverageReport(
            project_name=project_name,
            version=version,
            **analysis.get("coverage_report", {})
        )

        gap_report = GapReport(
            project_name=project_name,
            version=version,
            **analysis.get("gap_report", {})
        )

        risk_report = RiskReport(
            project_name=project_name,
            version=version,
            **analysis.get("risk_report", {})
        )

        # 2. Build Summary
        summary = QASummary(
            project_name=project_name,
            version=version,
            quality_score=quality_report.overall_score,
            coverage_score=coverage_report.coverage_score,
            gap_score=gap_report.gap_score,
            risk_score=risk_report.risk_score,
            critical_issues=quality_report.critical_issues,
            high_issues=quality_report.high_issues,
            medium_issues=quality_report.medium_issues,
            low_issues=quality_report.low_issues,
            status=quality_report.status,
        )

        # 3. Persist Outputs
        self.state_manager.save_qa_reports(
            summary=summary,
            quality=quality_report,
            coverage=coverage_report,
            gap=gap_report,
            risk=risk_report,
        )

        return QAAgentResult(
            provider=provider.provider_name,
            model=provider.model,
            summary=summary,
            quality_report=quality_report,
            coverage_report=coverage_report,
            gap_report=gap_report,
            risk_report=risk_report,
        )

    def _create_provider(self) -> BaseProvider:
        """Create the provider for the QA agent."""

        models = self.state_manager.load_models()
        assignment = models.assignment_for(AgentRole.QA)
        
        # Fallback to Master if QA is not explicitly configured
        if assignment is None or assignment.provider is None or assignment.model is None:
            assignment = models.assignment_for(AgentRole.MASTER)

        if assignment is None or assignment.provider is None or assignment.model is None:
            msg = "QA Agent requires QA or Master agent configuration."
            raise ProviderConfigurationError(msg)

        registry = self.provider_registry or build_default_provider_registry(self.settings)
        return registry.create(assignment.provider, model=assignment.model)

    def _parse_qa_response(self, response: str) -> dict[str, Any]:
        """Parse the JSON response from the provider."""

        normalized_response = response.strip()
        if not normalized_response:
            msg = "QA provider returned an empty response."
            raise ProviderRequestError(msg)

        try:
            payload = json.loads(normalized_response)
        except JSONDecodeError:
            payload = self._load_fenced_json_payload(normalized_response)

        if not isinstance(payload, dict):
            msg = "QA provider response must be a JSON object."
            raise ProviderRequestError(msg)
            
        return cast(dict[str, Any], payload)

    def _load_fenced_json_payload(self, response: str) -> Any:
        """Extract JSON from markdown code fences if present."""

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
                     return json.loads(response[first_brace:last_brace+1])
                 except JSONDecodeError:
                     pass
             msg = "QA provider returned non-JSON output."
             raise ProviderRequestError(msg)

        end_idx = -1
        for i in range(start_idx + 1, len(lines)):
            if lines[i].strip().startswith("```"):
                end_idx = i
                break
        
        if end_idx == -1:
            msg = "QA provider returned malformed fenced JSON."
            raise ProviderRequestError(msg)

        fenced_payload = "\n".join(lines[start_idx+1:end_idx]).strip()
        try:
            return json.loads(fenced_payload)
        except JSONDecodeError as exc:
            msg = "QA provider returned invalid JSON within fences."
            raise ProviderRequestError(msg) from exc
