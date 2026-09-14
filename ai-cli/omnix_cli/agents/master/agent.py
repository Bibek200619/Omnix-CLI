"""State-aware Master Agent implementation."""

from __future__ import annotations

from omnix_cli.agents.master.context_builder import MasterContextBuilder
from omnix_cli.agents.master.memory_manager import detect_memory_updates
from omnix_cli.agents.master.models import MasterAgentTurn
from omnix_cli.agents.master.prompts import build_master_system_prompt
from omnix_cli.core.settings import Settings
from omnix_cli.core.state_manager import StateManager
from omnix_cli.memory.memory_manager import MemoryManager
from omnix_cli.providers.exceptions import ProviderRequestError
from omnix_cli.providers.registry import ProviderRegistry, build_default_provider_registry
from omnix_cli.schemas.memory import ConversationRole, GoalStatus, ProjectDecision, ProjectGoal
from omnix_cli.schemas.tasks import AgentRole


class MasterAgent:
    """User-facing project manager backed by persistent memory."""

    def __init__(
        self,
        memory_manager: MemoryManager,
        *,
        state_manager: StateManager | None = None,
        context_builder: MasterContextBuilder | None = None,
        provider_registry: ProviderRegistry | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.memory_manager = memory_manager
        self.state_manager = state_manager or memory_manager.state_manager
        self.context_builder = context_builder or MasterContextBuilder(
            self.state_manager,
            memory_manager,
        )
        self.settings = settings or Settings()
        self.provider_registry = provider_registry

    async def handle_message(self, message: str) -> str:
        """Handle a user message, update memory, and return the Master response."""

        normalized_message = message.strip()
        if not normalized_message:
            msg = "Chat messages cannot be empty."
            raise ValueError(msg)

        self.memory_manager.add_conversation(ConversationRole.USER, normalized_message)

        updates = detect_memory_updates(normalized_message)
        recorded_goal = self._record_goal(updates.goal)
        recorded_decisions = [
            self.memory_manager.add_decision(decision) for decision in updates.decisions
        ]

        context = self.context_builder.build_context()
        provider_name, model_name, response = await self._generate_response(
            normalized_message,
            context,
            recorded_goal=recorded_goal,
            recorded_decisions=recorded_decisions,
        )

        self.memory_manager.add_conversation(ConversationRole.ASSISTANT, response)
        turn = MasterAgentTurn(
            user_message=normalized_message,
            assistant_response=response,
            detected_goal=recorded_goal.title if recorded_goal else None,
            detected_decisions=[decision.title for decision in recorded_decisions],
            provider=provider_name,
            model=model_name,
        )
        self.memory_manager.record_agent_output(
            role=AgentRole.MASTER,
            summary="Handled Master Agent conversation",
            content={
                **turn.model_dump(mode="json"),
                "phase": "2",
            },
        )
        return response

    def _record_goal(self, detected_goal: str | None) -> ProjectGoal | None:
        if detected_goal is None:
            return None
        return self.memory_manager.add_goal(detected_goal, status=GoalStatus.ACTIVE)

    async def _generate_response(
        self,
        message: str,
        context: str,
        *,
        recorded_goal: ProjectGoal | None,
        recorded_decisions: list[ProjectDecision],
    ) -> tuple[str | None, str | None, str]:
        models = self.state_manager.load_models()
        assignment = models.assignment_for(AgentRole.MASTER)
        if assignment is None or assignment.provider is None or assignment.model is None:
            return (
                None,
                None,
                self._build_local_response(
                    message,
                    recorded_goal=recorded_goal,
                    recorded_decisions=recorded_decisions,
                ),
            )

        registry = self.provider_registry or build_default_provider_registry(self.settings)
        provider = registry.create(assignment.provider, model=assignment.model)
        response = await provider.generate(
            message,
            system_prompt=build_master_system_prompt(context),
            temperature=0.2,
        )
        normalized_response = response.strip()
        if not normalized_response:
            msg = "Master provider returned an empty response."
            raise ProviderRequestError(msg)

        return provider.provider_name, provider.model, normalized_response

    def _build_local_response(
        self,
        message: str,
        *,
        recorded_goal: ProjectGoal | None,
        recorded_decisions: list[ProjectDecision],
    ) -> str:
        lower_message = message.casefold()
        memory = self.memory_manager.load_memory()
        active_goals = [goal for goal in memory.goals if goal.status == GoalStatus.ACTIVE]

        if self._asks_about_project_goal(lower_message) and active_goals:
            latest_goal = active_goals[-1]
            return (
                f"You previously recorded a goal to {latest_goal.title}. "
                "Implementation agents are not available yet in Phase 2, but I can "
                "continue tracking goals, decisions, and project context."
            )

        if recorded_goal is not None:
            return (
                f"Master Agent recorded the goal: {recorded_goal.title}. "
                "Phase 2 persistent memory is active. Configure the master role with "
                "`omnix config --set master=provider:model` for model-backed "
                "discussion. Implementation agents are not available yet."
            )

        if recorded_decisions:
            decision_text = ", ".join(decision.title for decision in recorded_decisions)
            return (
                f"Master Agent recorded the decision: {decision_text}. "
                "Phase 2 persistent memory is active. Implementation agents are not "
                "available yet."
            )

        return (
            "Master Agent recorded the conversation. Phase 2 persistent memory is "
            "active. Configure the master role with "
            "`omnix config --set master=provider:model` for model-backed discussion."
        )

    def _asks_about_project_goal(self, lower_message: str) -> bool:
        return any(
            phrase in lower_message
            for phrase in (
                "what are we building",
                "what is the goal",
                "what's the goal",
                "what are the goals",
                "what project",
            )
        )
