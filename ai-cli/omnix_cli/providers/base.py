"""Common provider contract."""

from __future__ import annotations

from abc import ABC, abstractmethod

from omnix_cli.core.settings import Settings
from omnix_cli.providers.exceptions import (
    ProviderAuthenticationError,
    ProviderConfigurationError,
)


class BaseProvider(ABC):
    """Base class for all LLM provider implementations."""

    def __init__(self, *, model: str, settings: Settings | None = None) -> None:
        normalized_model = model.strip()
        if not normalized_model:
            msg = "Provider model name cannot be empty."
            raise ProviderConfigurationError(msg)

        self.model = normalized_model
        self.settings = settings or Settings()

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider identifier used by model configuration."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.2,
    ) -> str:
        """Generate a text response from the provider."""

    def _validate_prompt(self, prompt: str) -> str:
        normalized_prompt = prompt.strip()
        if not normalized_prompt:
            msg = "Provider prompt cannot be empty."
            raise ProviderConfigurationError(msg)
        return normalized_prompt

    def _require_api_key(self, api_key: str | None, setting_name: str) -> str:
        if not api_key:
            msg = f"Missing {setting_name}. Set it in the environment or .env file."
            raise ProviderAuthenticationError(msg)
        return api_key
