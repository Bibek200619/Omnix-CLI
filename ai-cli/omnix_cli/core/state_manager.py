"""Validated project state persistence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from omnix_cli.core.exceptions import (
    ProjectAlreadyInitializedError,
    ProjectNotInitializedError,
    ProjectStateValidationError,
)
from omnix_cli.schemas.blueprint import ProjectBlueprint
from omnix_cli.schemas.memory import ProjectMemory
from omnix_cli.schemas.models import ModelsConfig
from omnix_cli.schemas.tasks import TaskPlan

ModelT = TypeVar("ModelT", bound=BaseModel)

PROJECT_DIR_NAME = ".project"
BLUEPRINT_FILE = "project.blueprint.json"
MEMORY_FILE = "project.memory.json"
MODELS_FILE = "models.json"
TASKS_FILE = "tasks.json"


class StateManager:
    """Owns all reads and writes for `.project` state."""

    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace.expanduser().resolve()
        self.project_dir = self.workspace / PROJECT_DIR_NAME
        self.blueprint_path = self.project_dir / BLUEPRINT_FILE
        self.memory_path = self.project_dir / MEMORY_FILE
        self.models_path = self.project_dir / MODELS_FILE
        self.tasks_path = self.project_dir / TASKS_FILE

    def init_project(
        self,
        project_name: str = "",
        description: str = "",
        force: bool = False,
    ) -> None:
        """Create the Phase 0 project state files."""

        existing_files = [
            self.blueprint_path,
            self.memory_path,
            self.models_path,
            self.tasks_path,
        ]
        if not force and any(path.exists() for path in existing_files):
            msg = (
                f"Project state already exists at {self.project_dir}. "
                "Use --force to overwrite Phase 0 state files."
            )
            raise ProjectAlreadyInitializedError(msg)

        self.project_dir.mkdir(parents=True, exist_ok=True)

        blueprint = ProjectBlueprint(project_name=project_name, description=description)
        memory = ProjectMemory(project_name=project_name)
        models = ModelsConfig()
        tasks = TaskPlan()

        self.save_blueprint(blueprint)
        self.save_memory(memory)
        self.save_models(models)
        self.save_tasks(tasks)

    def load_blueprint(self) -> ProjectBlueprint:
        """Load and validate `project.blueprint.json`."""

        return self._load_model(self.blueprint_path, ProjectBlueprint)

    def save_blueprint(self, blueprint: ProjectBlueprint) -> None:
        """Validate and persist `project.blueprint.json`."""

        self._write_model(self.blueprint_path, ProjectBlueprint.model_validate(blueprint))

    def load_memory(self) -> ProjectMemory:
        """Load and validate `project.memory.json`."""

        return self._load_model(self.memory_path, ProjectMemory)

    def save_memory(self, memory: ProjectMemory) -> None:
        """Validate and persist `project.memory.json`."""

        self._write_model(self.memory_path, ProjectMemory.model_validate(memory))

    def load_models(self) -> ModelsConfig:
        """Load and validate `models.json`."""

        return self._load_model(self.models_path, ModelsConfig)

    def save_models(self, models: ModelsConfig) -> None:
        """Validate and persist `models.json`."""

        self._write_model(self.models_path, ModelsConfig.model_validate(models))

    def load_tasks(self) -> TaskPlan:
        """Load and validate `tasks.json`."""

        if not self.tasks_path.exists() and self.project_dir.exists():
            return TaskPlan()
        return self._load_model(self.tasks_path, TaskPlan)

    def save_tasks(self, tasks: TaskPlan) -> None:
        """Validate and persist `tasks.json`."""

        self._write_model(self.tasks_path, TaskPlan.model_validate(tasks))

    def _load_model(self, path: Path, model_type: type[ModelT]) -> ModelT:
        if not path.exists():
            msg = f"Project state is not initialized. Missing {path}."
            raise ProjectNotInitializedError(msg)

        try:
            return model_type.model_validate_json(path.read_text(encoding="utf-8"))
        except ValidationError as exc:
            msg = f"Invalid project state in {path}: {exc}"
            raise ProjectStateValidationError(msg) from exc
        except OSError as exc:
            msg = f"Could not read project state from {path}: {exc}"
            raise ProjectStateValidationError(msg) from exc

    def _write_model(self, path: Path, model: BaseModel) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = model.model_dump(mode="json")
        encoded = json.dumps(payload, indent=2, sort_keys=False) + "\n"
        temporary_path = path.with_name(f".{path.name}.tmp")

        try:
            temporary_path.write_text(encoded, encoding="utf-8")
            temporary_path.replace(path)
        except OSError as exc:
            msg = f"Could not write project state to {path}: {exc}"
            raise ProjectStateValidationError(msg) from exc
