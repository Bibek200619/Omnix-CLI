"""Anthropic provider placeholder."""

from __future__ import annotations

from aicli.providers.base import BaseProvider
from aicli.providers.exceptions import ProviderRequestError


class AnthropicProvider(BaseProvider):
    """Anthropic provider boundary for future live generation support."""

    @property
    def provider_name(self) -> str:
        return "anthropic"

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.2,
    ) -> str:
        self._validate_prompt(prompt)
        self._require_api_key(self.settings.anthropic_api_key, "ANTHROPIC_API_KEY")
        msg = "Anthropic live generation is not implemented until a later provider adapter pass."
        raise ProviderRequestError(msg)
