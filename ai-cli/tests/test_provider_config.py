from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from omnix_cli.cli.main import app
from omnix_cli.schemas.models import ModelsConfig
from omnix_cli.schemas.tasks import AgentRole

runner = CliRunner()


def test_models_config_accepts_legacy_role_to_model_strings() -> None:
    models = ModelsConfig.model_validate({"master": "gpt-5"})

    assert models.model_for(AgentRole.MASTER) == "gpt-5"
    assert models.provider_for(AgentRole.MASTER) is None


def test_models_config_accepts_provider_model_assignments() -> None:
    models = ModelsConfig.model_validate(
        {"master": {"provider": "OpenAI", "model": "gpt-5"}}
    )

    assert models.provider_for(AgentRole.MASTER) == "openai"
    assert models.model_for(AgentRole.MASTER) == "gpt-5"


def test_config_preserves_legacy_json_output_while_persisting_provider(
    tmp_path: Path,
) -> None:
    runner.invoke(app, ["init", "--workspace", str(tmp_path)])

    result = runner.invoke(
        app,
        [
            "config",
            "--workspace",
            str(tmp_path),
            "--set",
            "master=openai:gpt-5",
            "--json",
        ],
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout)["master"] == "gpt-5"

    models = ModelsConfig.model_validate_json(
        (tmp_path / ".project" / "models.json").read_text(encoding="utf-8")
    )
    assert models.provider_for(AgentRole.MASTER) == "openai"
    assert models.model_for(AgentRole.MASTER) == "gpt-5"


def test_models_command_prints_provider_assignments(tmp_path: Path) -> None:
    runner.invoke(app, ["init", "--workspace", str(tmp_path)])
    runner.invoke(
        app,
        [
            "config",
            "--workspace",
            str(tmp_path),
            "--set",
            "frontend=google:gemini-2.5-pro",
        ],
    )

    result = runner.invoke(app, ["models", "--workspace", str(tmp_path)])

    assert result.exit_code == 0
    assert "frontend" in result.stdout
    assert "provider: google" in result.stdout
    assert "model: gemini-2.5-pro" in result.stdout
