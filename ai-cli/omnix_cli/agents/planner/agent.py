"""Planner Agent implementation."""

from __future__ import annotations

import json
from collections.abc import Mapping
from json import JSONDecodeError
from typing import cast

from pydantic import ValidationError

from omnix_cli.agents.planner.context_builder import PlannerContextBuilder
from omnix_cli.agents.planner.evolution import evolve_task_plan
from omnix_cli.agents.planner.models import PlannerAgentResult
from omnix_cli.agents.planner.prompts import (
    build_planner_system_prompt,
    build_planner_user_prompt,
)
from omnix_cli.agents.planner.validation import validate_task_plan
from omnix_cli.core.settings import Settings
from omnix_cli.core.state_manager import StateManager
from omnix_cli.memory.memory_manager import MemoryManager
from omnix_cli.providers.base import BaseProvider
from omnix_cli.providers.exceptions import ProviderConfigurationError, ProviderRequestError
from omnix_cli.providers.registry import ProviderRegistry, build_default_provider_registry
from omnix_cli.schemas.tasks import AgentRole, TaskAssignedAgent, TaskPlan


class PlannerAgent:
    """Generates and evolves the project task plan."""

    def __init__(
        self,
        state_manager: StateManager,
        *,
        memory_manager: MemoryManager | None = None,
        context_builder: PlannerContextBuilder | None = None,
        provider_registry: ProviderRegistry | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.state_manager = state_manager
        self.memory_manager = memory_manager or MemoryManager(state_manager)
        self.context_builder = context_builder or PlannerContextBuilder(
            state_manager,
            self.memory_manager,
        )
        self.provider_registry = provider_registry
        self.settings = settings or Settings()

    async def run(self) -> PlannerAgentResult:
        """Run the Planner Agent workflow."""

        return await self.generate_tasks()

    async def generate_tasks(self) -> PlannerAgentResult:
        """Generate, validate, persist, and report a task plan."""

        context = self.context_builder.build_context()
        provider = self._create_provider()
        response = await provider.generate(
            build_planner_user_prompt(context),
            system_prompt=build_planner_system_prompt(),
            temperature=0.1,
        )
        proposed_task_plan = self._parse_task_response(response)
        evolved = evolve_task_plan(context.existing_task_plan, proposed_task_plan)

        validate_task_plan(evolved.task_plan)
        self.state_manager.save_tasks(evolved.task_plan)

        result = PlannerAgentResult(
            provider=provider.provider_name,
            model=provider.model,
            task_plan=evolved.task_plan,
            task_count=len(evolved.task_plan.tasks),
            new_task_count=evolved.new_task_count,
            updated_task_count=evolved.updated_task_count,
            tasks_by_agent=self._count_tasks_by_agent(evolved.task_plan),
        )
        self.memory_manager.record_agent_output(
            role=AgentRole.PLANNER,
            summary="Generated task plan",
            content={
                "phase": "4",
                "provider": result.provider,
                "model": result.model,
                "task_count": result.task_count,
                "new_task_count": result.new_task_count,
                "updated_task_count": result.updated_task_count,
                "tasks_by_agent": result.tasks_by_agent,
            },
        )
        return result

    def _create_provider(self) -> BaseProvider:
        models = self.state_manager.load_models()
        assignment = models.assignment_for(AgentRole.PLANNER)
        if assignment is None or assignment.provider is None or assignment.model is None:
            msg = (
                "Role 'planner' is missing provider/model configuration. "
                "Use `omnix config --set planner=provider:model` first."
            )
            raise ProviderConfigurationError(msg)

        registry = self.provider_registry or build_default_provider_registry(self.settings)
        return registry.create(assignment.provider, model=assignment.model)

    def _parse_task_response(self, response: str) -> TaskPlan:
        normalized_response = response.strip()
        if not normalized_response:
            msg = "Planner provider returned an empty response."
            raise ProviderRequestError(msg)

        payload = self._load_json_payload(normalized_response)
        if isinstance(payload, list):
            payload = {"tasks": payload}
        try:
            return TaskPlan.model_validate(payload)
        except ValidationError as exc:
            msg = f"Planner provider returned invalid task JSON: {exc}"
            raise ProviderRequestError(msg) from exc

    def _load_json_payload(self, response: str) -> Mapping[str, object] | list[object]:
        try:
            payload = json.loads(response)
        except JSONDecodeError:
            payload = self._load_fenced_json_payload(response)

        if not isinstance(payload, Mapping | list):
            msg = "Planner provider response must be a JSON object or array."
            raise ProviderRequestError(msg)
        return cast(Mapping[str, object] | list[object], payload)

    def _load_fenced_json_payload(self, response: str) -> object:
        lines = response.splitlines()
        if len(lines) < 3:
            msg = "Planner provider returned non-JSON output."
            raise ProviderRequestError(msg)

        first_line = lines[0].strip()
        last_line = lines[-1].strip()
        if not first_line.startswith("```") or last_line != "```":
            msg = "Planner provider returned non-JSON output."
            raise ProviderRequestError(msg)

        fenced_payload = "\n".join(lines[1:-1]).strip()
        try:
            return json.loads(fenced_payload)
        except JSONDecodeError as exc:
            msg = "Planner provider returned non-JSON output."
            raise ProviderRequestError(msg) from exc

    def _count_tasks_by_agent(self, task_plan: TaskPlan) -> dict[str, int]:
        counts = {agent.value: 0 for agent in TaskAssignedAgent}
        for task in task_plan.tasks:
            counts[task.assigned_agent.value] += 1
        return {agent: count for agent, count in counts.items() if count > 0}
