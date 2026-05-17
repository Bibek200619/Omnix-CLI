from __future__ import annotations

import asyncio
import json

import httpx
import pytest

from aicli.core.settings import Settings
from aicli.providers.base import BaseProvider
from aicli.providers.exceptions import (
    ProviderAuthenticationError,
    ProviderConfigurationError,
)
from aicli.providers.openai import OpenAIProvider
from aicli.providers.registry import ProviderRegistry, build_default_provider_registry


class MockProvider(BaseProvider):
    @property
    def provider_name(self) -> str:
        return "mock"

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.2,
    ) -> str:
        self._validate_prompt(prompt)
        return f"{self.provider_name}:{self.model}"


def test_registry_registers_resolves_and_creates_provider() -> None:
    registry = ProviderRegistry(settings=Settings())
    registry.register("mock", MockProvider)

    provider = registry.create("MOCK", model="test-model")

    assert isinstance(provider, MockProvider)
    assert provider.provider_name == "mock"
    assert provider.model == "test-model"


def test_registry_rejects_unknown_provider() -> None:
    registry = ProviderRegistry()

    with pytest.raises(ProviderConfigurationError, match="Unknown provider"):
        registry.create("missing", model="test-model")


def test_default_registry_contains_phase_1_providers() -> None:
    registry = build_default_provider_registry(Settings())

    assert registry.provider_names == (
        "anthropic",
        "deepseek",
        "google",
        "openai",
        "openrouter",
    )


def test_openai_provider_requires_api_key() -> None:
    provider = OpenAIProvider(model="gpt-5", settings=Settings(openai_api_key=None))

    with pytest.raises(ProviderAuthenticationError, match="OPENAI_API_KEY"):
        asyncio.run(provider.generate("hello"))


def test_openai_provider_generates_with_mock_transport() -> None:
    async def run_generation() -> str:
        async def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content)
            assert request.url == httpx.URL("https://api.example.test/responses")
            assert request.headers["authorization"] == "Bearer test-key"
            assert body["model"] == "gpt-5"
            return httpx.Response(200, json={"output_text": "hello from openai"})

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        provider = OpenAIProvider(
            model="gpt-5",
            settings=Settings(
                openai_api_key="test-key",
                openai_base_url="https://api.example.test",
            ),
            client=client,
        )
        try:
            return await provider.generate("hello")
        finally:
            await client.aclose()

    assert asyncio.run(run_generation()) == "hello from openai"
