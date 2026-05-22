"""Provider registry and construction helpers."""

from __future__ import annotations

from omnix_cli.core.settings import Settings
from omnix_cli.providers.base import BaseProvider
from omnix_cli.providers.exceptions import ProviderConfigurationError


class ProviderRegistry:
    """Maps provider names to provider implementation classes."""

    def __init__(self, *, settings: Settings | None = None) -> None:
        self._providers: dict[str, type[BaseProvider]] = {}
        self._settings = settings

    def register(self, name: str, provider_type: type[BaseProvider]) -> None:
        """Register a provider implementation by name."""

        normalized_name = self._normalize_name(name)
        if not issubclass(provider_type, BaseProvider):
            msg = f"Provider '{name}' must inherit from BaseProvider."
            raise ProviderConfigurationError(msg)
        self._providers[normalized_name] = provider_type

    def resolve(self, name: str) -> type[BaseProvider]:
        """Resolve a provider implementation by name."""

        normalized_name = self._normalize_name(name)
        try:
            return self._providers[normalized_name]
        except KeyError as exc:
            available = ", ".join(sorted(self._providers)) or "<none>"
            msg = f"Unknown provider '{name}'. Registered providers: {available}."
            raise ProviderConfigurationError(msg) from exc

    def create(
        self,
        name: str,
        *,
        model: str,
        settings: Settings | None = None,
    ) -> BaseProvider:
        """Instantiate a provider through the registry."""

        provider_type = self.resolve(name)
        return provider_type(model=model, settings=settings or self._settings)

    @property
    def provider_names(self) -> tuple[str, ...]:
        """Return registered provider names in stable order."""

        return tuple(sorted(self._providers))

    def _normalize_name(self, name: str) -> str:
        normalized_name = name.strip().lower()
        if not normalized_name:
            msg = "Provider name cannot be empty."
            raise ProviderConfigurationError(msg)
        return normalized_name


def build_default_provider_registry(settings: Settings | None = None) -> ProviderRegistry:
    """Create the built-in provider registry."""

    from omnix_cli.providers.anthropic import AnthropicProvider
    from omnix_cli.providers.deepseek import DeepSeekProvider
    from omnix_cli.providers.google import GoogleProvider
    from omnix_cli.providers.openai import OpenAIProvider
    from omnix_cli.providers.openrouter import OpenRouterProvider

    registry = ProviderRegistry(settings=settings)
    registry.register("openai", OpenAIProvider)
    registry.register("anthropic", AnthropicProvider)
    registry.register("google", GoogleProvider)
    registry.register("openrouter", OpenRouterProvider)
    registry.register("deepseek", DeepSeekProvider)
    return registry
