"""OpenRouter provider placeholder."""

from __future__ import annotations

from omnix_cli.providers.base import BaseProvider
from omnix_cli.providers.exceptions import ProviderRequestError


class OpenRouterProvider(BaseProvider):
    """OpenRouter provider boundary for future live generation support."""

    @property
    def provider_name(self) -> str:
        return "openrouter"

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.2,
    ) -> str:
        self._validate_prompt(prompt)
        self._require_api_key(self.settings.openrouter_api_key, "OPENROUTER_API_KEY")
        msg = "OpenRouter live generation is not implemented until a later provider adapter pass."
        raise ProviderRequestError(msg)
