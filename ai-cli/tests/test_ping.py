from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

import omnix_cli.cli.commands.ping as ping_module
from omnix_cli.cli.main import app
from omnix_cli.core.settings import Settings
from omnix_cli.providers.base import BaseProvider
from omnix_cli.providers.registry import ProviderRegistry

runner = CliRunner()


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
        return "mock provider ready"


def test_ping_uses_role_provider_configuration(
    tmp_path: Path,
    monkeypatch,
) -> None:
    runner.invoke(app, ["init", "--workspace", str(tmp_path)])
    runner.invoke(
        app,
        [
            "config",
            "--workspace",
            str(tmp_path),
            "--set",
            "master=mock:test-model",
        ],
    )

    def build_registry(settings: Settings | None = None) -> ProviderRegistry:
        registry = ProviderRegistry(settings=settings)
        registry.register("mock", MockProvider)
        return registry

    monkeypatch.setattr(ping_module, "build_default_provider_registry", build_registry)

    result = runner.invoke(app, ["ping", "master", "--workspace", str(tmp_path)])

    assert result.exit_code == 0
    assert "Role: master" in result.stdout
    assert "Provider: mock" in result.stdout
    assert "Model: test-model" in result.stdout
    assert "mock provider ready" in result.stdout


def test_ping_requires_provider_and_model_configuration(tmp_path: Path) -> None:
    runner.invoke(app, ["init", "--workspace", str(tmp_path)])

    result = runner.invoke(app, ["ping", "master", "--workspace", str(tmp_path)])

    assert result.exit_code == 1
    assert "missing provider/model configuration" in result.stderr
