"""Architect Agent implementation."""

from __future__ import annotations

import json
from collections.abc import Mapping
from json import JSONDecodeError
from typing import cast

from pydantic import ValidationError

from omnix_cli.agents.architect.context_builder import ArchitectContextBuilder
from omnix_cli.agents.architect.models import ArchitectAgentResult
from omnix_cli.agents.architect.prompts import (
    build_architect_system_prompt,
    build_architect_user_prompt,
)
from omnix_cli.blueprint.evolution import evolve_blueprint
from omnix_cli.blueprint.validation import validate_architecture_blueprint
from omnix_cli.core.settings import Settings
from omnix_cli.core.state_manager import StateManager
from omnix_cli.memory.memory_manager import MemoryManager
from omnix_cli.providers.base import BaseProvider
from omnix_cli.providers.exceptions import ProviderConfigurationError, ProviderRequestError
from omnix_cli.providers.registry import ProviderRegistry, build_default_provider_registry
from omnix_cli.schemas.blueprint import GoalDefinition, ProjectBlueprint
from omnix_cli.schemas.tasks import AgentRole


class ArchitectAgent:
    """Generates and evolves the project architecture blueprint."""

    def __init__(
        self,
        state_manager: StateManager,
        *,
        memory_manager: MemoryManager | None = None,
        context_builder: ArchitectContextBuilder | None = None,
        provider_registry: ProviderRegistry | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.state_manager = state_manager
        self.memory_manager = memory_manager or MemoryManager(state_manager)
        self.context_builder = context_builder or ArchitectContextBuilder(
            state_manager,
            self.memory_manager,
        )
        self.provider_registry = provider_registry
        self.settings = settings or Settings()

    async def run(self) -> ArchitectAgentResult:
        """Run the Architect Agent workflow."""

        return await self.generate_blueprint()

    async def generate_blueprint(self) -> ArchitectAgentResult:
        """Generate, validate, persist, and report a project blueprint."""

        context = self.context_builder.build_context()
        provider = self._create_provider()
        response = await provider.generate(
            build_architect_user_prompt(context),
            system_prompt=build_architect_system_prompt(),
            temperature=0.1,
        )
        proposed_blueprint = self._parse_blueprint_response(response)
        evolved_blueprint = evolve_blueprint(
            context.existing_blueprint,
            proposed_blueprint,
        )
        evolved_blueprint = evolve_blueprint(
            evolved_blueprint,
            ProjectBlueprint(
                goals=[GoalDefinition(title=goal) for goal in context.goals],
            ),
        )

        validate_architecture_blueprint(evolved_blueprint)
        self.state_manager.save_blueprint(evolved_blueprint)

        result = ArchitectAgentResult(
            provider=provider.provider_name,
            model=provider.model,
            blueprint=evolved_blueprint,
            feature_count=len(evolved_blueprint.features),
            entity_count=len(evolved_blueprint.entities),
            module_count=len(evolved_blueprint.modules),
            architecture_note_count=len(evolved_blueprint.architecture_notes),
        )
        self.memory_manager.record_agent_output(
            role=AgentRole.ARCHITECT,
            summary="Generated architecture blueprint",
            content={
                "phase": "3",
                "provider": result.provider,
                "model": result.model,
                "project_name": result.blueprint.project_name,
                "feature_count": result.feature_count,
                "entity_count": result.entity_count,
                "module_count": result.module_count,
                "architecture_note_count": result.architecture_note_count,
            },
        )
        return result

    def _create_provider(self) -> BaseProvider:
        models = self.state_manager.load_models()
        assignment = models.assignment_for(AgentRole.ARCHITECT)
        if assignment is None or assignment.provider is None or assignment.model is None:
            msg = (
                "Role 'architect' is missing provider/model configuration. "
                "Use `omnix config --set architect=provider:model` first."
            )
            raise ProviderConfigurationError(msg)

        registry = self.provider_registry or build_default_provider_registry(self.settings)
        return registry.create(assignment.provider, model=assignment.model)

    def _parse_blueprint_response(self, response: str) -> ProjectBlueprint:
        normalized_response = response.strip()
        if not normalized_response:
            msg = "Architect provider returned an empty response."
            raise ProviderRequestError(msg)

        payload = self._load_json_object(normalized_response)
        try:
            return ProjectBlueprint.model_validate(payload)
        except ValidationError as exc:
            msg = f"Architect provider returned invalid blueprint JSON: {exc}"
            raise ProviderRequestError(msg) from exc

    def _load_json_object(self, response: str) -> Mapping[str, object]:
        try:
            payload = json.loads(response)
        except JSONDecodeError:
            payload = self._load_fenced_json_object(response)

        if not isinstance(payload, Mapping):
            msg = "Architect provider response must be a JSON object."
            raise ProviderRequestError(msg)
        return cast(Mapping[str, object], payload)

    def _load_fenced_json_object(self, response: str) -> object:
        lines = response.splitlines()
        if len(lines) < 3:
            msg = "Architect provider returned non-JSON output."
            raise ProviderRequestError(msg)

        first_line = lines[0].strip()
        last_line = lines[-1].strip()
        if not first_line.startswith("```") or last_line != "```":
            msg = "Architect provider returned non-JSON output."
            raise ProviderRequestError(msg)

        fenced_payload = "\n".join(lines[1:-1]).strip()
        try:
            return json.loads(fenced_payload)
        except JSONDecodeError as exc:
            msg = "Architect provider returned non-JSON output."
            raise ProviderRequestError(msg) from exc
