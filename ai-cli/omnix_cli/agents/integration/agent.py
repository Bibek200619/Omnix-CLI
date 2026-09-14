"""Integration Agent implementation."""

from __future__ import annotations

import json
from json import JSONDecodeError
from typing import Any, cast

from omnix_cli.agents.integration.context_builder import IntegrationContextBuilder
from omnix_cli.agents.integration.models import IntegrationAgentResult
from omnix_cli.agents.integration.prompts import (
    build_integration_system_prompt,
    build_integration_user_prompt,
)
from omnix_cli.core.settings import Settings
from omnix_cli.core.state_manager import StateManager
from omnix_cli.providers.base import BaseProvider
from omnix_cli.providers.exceptions import ProviderConfigurationError, ProviderRequestError
from omnix_cli.providers.registry import ProviderRegistry, build_default_provider_registry
from omnix_cli.schemas.integration import (
    Conflict,
    ConflictReport,
    CoverageSummary,
    Dependency,
    DependencyGraph,
    IntegratedPackage,
    IntegrationReport,
    IntegrationStatus,
)
from omnix_cli.schemas.tasks import AgentRole


class IntegrationAgent:
    """Orchestration agent that assembles worker artifacts into an Integrated Package."""

    def __init__(
        self,
        state_manager: StateManager,
        *,
        context_builder: IntegrationContextBuilder | None = None,
        provider_registry: ProviderRegistry | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.state_manager = state_manager
        self.context_builder = context_builder or IntegrationContextBuilder(state_manager)
        self.provider_registry = provider_registry
        self.settings = settings or Settings()

    async def integrate(self) -> IntegrationAgentResult:
        """Analyze all artifacts and produce the integrated package."""

        context = self.context_builder.build_context()
        provider = self._create_provider()
        
        response = await provider.generate(
            build_integration_user_prompt(
                context["project_name"],
                context["blueprint"],
                context["artifacts"],
                context["tasks"],
            ),
            system_prompt=build_integration_system_prompt(),
            temperature=0.1,
        )
        
        analysis = self._parse_integration_response(response)
        
        blueprint = self.state_manager.load_blueprint()
        artifacts = self.state_manager.list_artifacts()
        
        # 1. Build Coverage Summary
        coverage = CoverageSummary(
            total_pages=len(blueprint.pages),
            implemented_pages=analysis.get("coverage", {}).get("implemented_pages", 0),
            total_apis=len(blueprint.apis),
            implemented_apis=analysis.get("coverage", {}).get("implemented_apis", 0),
            total_entities=len(blueprint.entities),
            implemented_entities=analysis.get("coverage", {}).get("implemented_entities", 0),
            gaps=analysis.get("coverage", {}).get("gaps", []),
        )

        # 2. Build Dependencies
        dependencies = [
            Dependency(**d) for d in analysis.get("dependencies", [])
        ]

        # 3. Build Conflicts
        conflicts = [
            Conflict(**c) for c in analysis.get("conflicts", [])
        ]

        # 4. Assemble Integrated Package
        package = IntegratedPackage(
            project_name=blueprint.project_name,
            pages=[p.model_dump() for p in blueprint.pages],
            features=[f.model_dump() for f in blueprint.features],
            entities=[e.model_dump() for e in blueprint.entities],
            apis=[a.model_dump() for a in blueprint.apis],
            # In blueprint, pages often represent routes
            routes=[r.model_dump() for r in blueprint.pages],
            workflows=[], # Future expansion
            dependencies=dependencies,
            artifacts=artifacts,
            conflicts=conflicts,
            coverage=coverage,
            status=cast(IntegrationStatus, analysis.get("status", IntegrationStatus.SUCCESS)),
        )

        # 5. Build Dependency Graph
        # Simplified: nodes are artifacts + blueprint entities
        nodes = []
        for a in artifacts:
            nodes.append({"id": a.id, "type": "artifact", "label": a.title})
        for e in blueprint.entities:
            nodes.append({"id": f"entity_{e.name}", "type": "entity", "label": e.name})
            
        graph = DependencyGraph(nodes=nodes, edges=dependencies)

        # 6. Build Reports
        conflict_report = ConflictReport(
            project_name=blueprint.project_name,
            total_conflicts=len(conflicts),
            conflicts=conflicts,
        )

        artifacts_by_agent: dict[str, int] = {}
        for a in artifacts:
            artifacts_by_agent[a.agent] = artifacts_by_agent.get(a.agent, 0) + 1

        integration_report = IntegrationReport(
            project_name=blueprint.project_name,
            status=package.status,
            artifacts_processed=len(artifacts),
            artifacts_by_agent=artifacts_by_agent,
            dependencies_found=len(dependencies),
            conflicts_found=len(conflicts),
            coverage_status="COMPLETE" if not coverage.gaps else "INCOMPLETE",
            summary=analysis.get("summary", "Integration completed."),
        )

        # 7. Persist Outputs
        self.state_manager.save_integrated_package(package)
        self.state_manager.save_dependency_graph(graph)
        self.state_manager.save_integration_report(integration_report)
        self.state_manager.save_conflict_report(conflict_report)

        return IntegrationAgentResult(
            provider=provider.provider_name,
            model=provider.model,
            package=package,
            dependency_graph=graph,
            integration_report=integration_report,
            conflict_report=conflict_report,
        )

    def _create_provider(self) -> BaseProvider:
        # Integration usually uses Master or a specialized model
        # We'll try Master, fallback to Google
        models = self.state_manager.load_models()
        assignment = models.assignment_for(AgentRole.MASTER)
        
        if assignment is None or assignment.provider is None or assignment.model is None:
            # Fallback to config or error
            msg = "Integration requires Master agent configuration."
            raise ProviderConfigurationError(msg)

        registry = self.provider_registry or build_default_provider_registry(self.settings)
        return registry.create(assignment.provider, model=assignment.model)

    def _parse_integration_response(self, response: str) -> dict[str, Any]:
        normalized_response = response.strip()
        if not normalized_response:
            msg = "Integration provider returned an empty response."
            raise ProviderRequestError(msg)

        try:
            payload = json.loads(normalized_response)
        except JSONDecodeError:
            payload = self._load_fenced_json_payload(normalized_response)

        if not isinstance(payload, dict):
            msg = "Integration provider response must be a JSON object."
            raise ProviderRequestError(msg)
            
        return cast(dict[str, Any], payload)

    def _load_fenced_json_payload(self, response: str) -> Any:
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
             msg = "Integration provider returned non-JSON output."
             raise ProviderRequestError(msg)

        end_idx = -1
        for i in range(start_idx + 1, len(lines)):
            if lines[i].strip().startswith("```"):
                end_idx = i
                break
        
        if end_idx == -1:
            msg = "Integration provider returned malformed fenced JSON."
            raise ProviderRequestError(msg)

        fenced_payload = "\n".join(lines[start_idx+1:end_idx]).strip()
        try:
            return json.loads(fenced_payload)
        except JSONDecodeError as exc:
            msg = "Integration provider returned invalid JSON within fences."
            raise ProviderRequestError(msg) from exc
