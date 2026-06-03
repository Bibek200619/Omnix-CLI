"""Tests for artifact CLI commands."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from omnix_cli.cli.main import app
from omnix_cli.core.state_manager import StateManager
from omnix_cli.schemas.artifacts import Artifact, ArtifactType

runner = CliRunner()


def test_artifacts_list_empty(tmp_path: Path) -> None:
    _initialized_project(tmp_path)
    result = runner.invoke(app, ["artifacts", "-w", str(tmp_path)])
    assert result.exit_code == 0
    assert "No artifacts found." in result.stdout


def test_artifacts_list_with_content(tmp_path: Path) -> None:
    state_manager = _initialized_project(tmp_path)
    artifact = Artifact(
        id="art_001",
        task_id="task_001",
        agent="frontend",
        title="Test Artifact",
        artifact_type=ArtifactType.FRONTEND_COMPONENT,
        content="some content",
    )
    state_manager.save_artifact(artifact)

    result = runner.invoke(app, ["artifacts", "-w", str(tmp_path)])
    assert result.exit_code == 0
    assert "art_001" in result.stdout
    assert "Test Artifact" in result.stdout
    assert "frontend" in result.stdout


def test_artifact_view(tmp_path: Path) -> None:
    state_manager = _initialized_project(tmp_path)
    artifact = Artifact(
        id="art_001",
        task_id="task_001",
        agent="frontend",
        title="Test Artifact",
        description="Detailed description",
        artifact_type=ArtifactType.FRONTEND_COMPONENT,
        content="export const Test = () => <div>Test</div>;",
        metadata={"key": "value"}
    )
    state_manager.save_artifact(artifact)

    result = runner.invoke(app, ["artifact", "art_001", "-w", str(tmp_path)])
    assert result.exit_code == 0
    assert "Artifact: Test Artifact" in result.stdout
    assert "ID:           art_001" in result.stdout
    assert "Detailed description" in result.stdout
    assert ' "key": "value"' in result.stdout
    assert "export const Test" in result.stdout


def test_artifact_view_not_found(tmp_path: Path) -> None:
    _initialized_project(tmp_path)
    result = runner.invoke(app, ["artifact", "missing", "-w", str(tmp_path)])
    assert result.exit_code == 1
    assert "Artifact 'missing' not found." in result.stderr


def _initialized_project(tmp_path: Path) -> StateManager:
    state_manager = StateManager(tmp_path)
    state_manager.init_project(project_name="Test")
    return state_manager
