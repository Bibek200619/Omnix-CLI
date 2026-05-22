from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from omnix_cli.cli.main import app
from omnix_cli.schemas.blueprint import ProjectBlueprint
from omnix_cli.schemas.memory import ProjectMemory
from omnix_cli.schemas.models import ModelsConfig

runner = CliRunner()


def test_init_creates_valid_project_state(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "init",
            "--workspace",
            str(tmp_path),
            "--project-name",
            "CRM",
            "--description",
            "SaaS CRM",
        ],
    )

    assert result.exit_code == 0
    project_dir = tmp_path / ".project"
    assert project_dir.is_dir()

    blueprint = ProjectBlueprint.model_validate_json(
        (project_dir / "project.blueprint.json").read_text(encoding="utf-8")
    )
    memory = ProjectMemory.model_validate_json(
        (project_dir / "project.memory.json").read_text(encoding="utf-8")
    )
    models = ModelsConfig.model_validate_json((project_dir / "models.json").read_text())

    assert blueprint.project_name == "CRM"
    assert blueprint.description == "SaaS CRM"
    assert memory.project_name == "CRM"
    assert models.master is None


def test_init_refuses_to_overwrite_without_force(tmp_path: Path) -> None:
    first = runner.invoke(app, ["init", "--workspace", str(tmp_path)])
    second = runner.invoke(app, ["init", "--workspace", str(tmp_path)])

    assert first.exit_code == 0
    assert second.exit_code == 1
    assert "already exists" in second.stderr


def test_config_updates_and_prints_models(tmp_path: Path) -> None:
    runner.invoke(app, ["init", "--workspace", str(tmp_path)])

    result = runner.invoke(
        app,
        [
            "config",
            "--workspace",
            str(tmp_path),
            "--set",
            "master=gpt-5",
            "--set",
            "qa=gpt-5",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["master"] == "gpt-5"
    assert payload["qa"] == "gpt-5"


def test_config_rejects_unknown_roles(tmp_path: Path) -> None:
    runner.invoke(app, ["init", "--workspace", str(tmp_path)])

    result = runner.invoke(
        app,
        ["config", "--workspace", str(tmp_path), "--set", "mobile=gpt-5"],
    )

    assert result.exit_code == 1
    assert "Unknown role" in result.stderr


def test_chat_records_master_output_in_memory(tmp_path: Path) -> None:
    runner.invoke(app, ["init", "--workspace", str(tmp_path), "--project-name", "CRM"])

    result = runner.invoke(
        app,
        ["chat", "--workspace", str(tmp_path), "Build authentication"],
    )

    assert result.exit_code == 0
    assert "Master Agent recorded the goal" in result.stdout

    memory = ProjectMemory.model_validate_json(
        (tmp_path / ".project" / "project.memory.json").read_text(encoding="utf-8")
    )
    assert len(memory.agent_outputs) == 1
    output = memory.agent_outputs[0]
    assert output.role == "master"
    assert output.content["user_message"] == "Build authentication"
