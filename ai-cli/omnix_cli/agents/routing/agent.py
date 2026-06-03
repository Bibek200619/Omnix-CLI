"""Routing Agent implementation."""

from __future__ import annotations

import json
from json import JSONDecodeError
from typing import Any, cast

from omnix_cli.agents.routing.context_builder import RoutingContextBuilder
from omnix_cli.agents.routing.models import RoutingAgentResult
from omnix_cli.agents.routing.prompts import (
    build_routing_system_prompt,
    build_routing_user_prompt,
)
from omnix_cli.core.settings import Settings
from omnix_cli.core.state_manager import StateManager
from omnix_cli.memory.memory_manager import MemoryManager
from omnix_cli.providers.base import BaseProvider
from omnix_cli.providers.exceptions import ProviderConfigurationError, ProviderRequestError
from omnix_cli.providers.registry import ProviderRegistry, build_default_provider_registry
from omnix_cli.schemas.artifacts import Artifact, ArtifactType
from omnix_cli.schemas.tasks import AgentRole, TaskDefinition


class RoutingAgent:
    """Worker agent that generates routing artifacts."""

    def __init__(
        self,
        state_manager: StateManager,
        *,
        memory_manager: MemoryManager | None = None,
        context_builder: RoutingContextBuilder | None = None,
        provider_registry: ProviderRegistry | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.state_manager = state_manager
        self.memory_manager = memory_manager or MemoryManager(state_manager)
        self.context_builder = context_builder or RoutingContextBuilder(
            state_manager,
            self.memory_manager,
        )
        self.provider_registry = provider_registry
        self.settings = settings or Settings()

    async def execute_task(self, task: TaskDefinition) -> RoutingAgentResult:
        """Execute a routing task and produce an artifact."""

        if task.assigned_agent.value != AgentRole.ROUTING.value:
            msg = f"Task {task.id} is not assigned to the Routing Agent."
            raise ValueError(msg)

        context = self.context_builder.build_context()
        provider = self._create_provider()
        
        task_description = f"Title: {task.title}\nDescription: {task.description}"
        
        response = await provider.generate(
            build_routing_user_prompt(context, task_description),
            system_prompt=build_routing_system_prompt(),
            temperature=0.2,
        )
        
        artifact_data = self._parse_artifact_response(response)
        
        # Build artifact model
        version = self.state_manager.get_next_artifact_version(task.id)
        artifact_id = f"art_{task.id}_{version}"
        
        artifact_type = cast(
            ArtifactType,
            artifact_data.get("artifact_type", ArtifactType.ROUTE_MAP),
        )

        artifact = Artifact(
            id=artifact_id,
            task_id=task.id,
            agent=AgentRole.ROUTING,
            title=artifact_data.get("title", task.title),
            description=artifact_data.get("description", ""),
            artifact_type=artifact_type,
            content=artifact_data.get("content", ""),
            metadata=artifact_data.get("metadata", {}),
            version=version,
        )
        
        self.state_manager.save_artifact(artifact)
        
        result = RoutingAgentResult(
            provider=provider.provider_name,
            model=provider.model,
            artifact=artifact,
            task_id=task.id,
        )
        
        self.memory_manager.record_agent_output(
            role=AgentRole.ROUTING,
            summary=f"Generated artifact for task {task.id}",
            content={
                "task_id": task.id,
                "artifact_id": artifact.id,
                "artifact_type": artifact.artifact_type,
                "provider": result.provider,
                "model": result.model,
            },
        )
        
        return result

    def _create_provider(self) -> BaseProvider:
        models = self.state_manager.load_models()
        assignment = models.assignment_for(AgentRole.ROUTING)
        
        if assignment is None or assignment.provider is None or assignment.model is None:
            msg = (
                "Role 'routing' is missing provider/model configuration. "
                "Use `omnix config --set routing=provider:model` first."
            )
            raise ProviderConfigurationError(msg)

        registry = self.provider_registry or build_default_provider_registry(self.settings)
        return registry.create(assignment.provider, model=assignment.model)

    def _parse_artifact_response(self, response: str) -> dict[str, Any]:
        normalized_response = response.strip()
        if not normalized_response:
            msg = "Routing provider returned an empty response."
            raise ProviderRequestError(msg)

        try:
            payload = json.loads(normalized_response)
        except JSONDecodeError:
            payload = self._load_fenced_json_payload(normalized_response)

        if not isinstance(payload, dict):
            msg = "Routing provider response must be a JSON object."
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
             msg = "Routing provider returned non-JSON output."
             raise ProviderRequestError(msg)

        end_idx = -1
        for i in range(start_idx + 1, len(lines)):
            if lines[i].strip().startswith("```"):
                end_idx = i
                break
        
        if end_idx == -1:
            msg = "Routing provider returned malformed fenced JSON."
            raise ProviderRequestError(msg)

        fenced_payload = "\n".join(lines[start_idx+1:end_idx]).strip()
        try:
            return json.loads(fenced_payload)
        except JSONDecodeError as exc:
            msg = "Routing provider returned invalid JSON within fences."
            raise ProviderRequestError(msg) from exc
