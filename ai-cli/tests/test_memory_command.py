from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from aicli.cli.main import app

runner = CliRunner()


def test_memory_goals_and_decisions_commands_display_persisted_state(
    tmp_path: Path,
) -> None:
    runner.invoke(app, ["init", "--workspace", str(tmp_path), "--project-name", "CRM"])
    runner.invoke(app, ["chat", "--workspace", str(tmp_path), "Build SaaS CRM"])
    runner.invoke(app, ["chat", "--workspace", str(tmp_path), "We will use FastAPI."])

    memory_result = runner.invoke(app, ["memory", "--workspace", str(tmp_path)])
    goals_result = runner.invoke(app, ["goals", "--workspace", str(tmp_path)])
    decisions_result = runner.invoke(app, ["decisions", "--workspace", str(tmp_path)])

    assert memory_result.exit_code == 0
    assert "Project Goals" in memory_result.stdout
    assert "* Build SaaS CRM" in memory_result.stdout
    assert "Recent Decisions" in memory_result.stdout
    assert "* Use FastAPI" in memory_result.stdout
    assert "4 stored messages" in memory_result.stdout

    assert goals_result.exit_code == 0
    assert "Active Goals" in goals_result.stdout
    assert "1. Build SaaS CRM" in goals_result.stdout

    assert decisions_result.exit_code == 0
    assert "Project Decisions" in decisions_result.stdout
    assert "* Use FastAPI" in decisions_result.stdout
