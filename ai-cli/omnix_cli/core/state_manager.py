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
from omnix_cli.schemas.artifacts import Artifact
from omnix_cli.schemas.blueprint import ProjectBlueprint
from omnix_cli.schemas.integration import (
    ConflictReport,
    DependencyGraph,
    IntegratedPackage,
    IntegrationReport,
)
from omnix_cli.schemas.memory import ProjectMemory
from omnix_cli.schemas.models import ModelsConfig
from omnix_cli.schemas.qa import (
    CoverageReport,
    GapReport,
    QASummary,
    QualityReport,
    RiskReport,
)
from omnix_cli.schemas.repair import (
    RepairArtifact,
    RepairHistory,
    RepairPlan,
    RepairReport,
)
from omnix_cli.schemas.tasks import TaskPlan

ModelT = TypeVar("ModelT", bound=BaseModel)

PROJECT_DIR_NAME = ".project"
ARTIFACTS_DIR_NAME = "artifacts"
INTEGRATION_DIR_NAME = "integration"
QA_DIR_NAME = "qa"
QA_HISTORY_DIR_NAME = "history"
REPAIR_DIR_NAME = "repair"
BLUEPRINT_FILE = "project.blueprint.json"
MEMORY_FILE = "project.memory.json"
MODELS_FILE = "models.json"
TASKS_FILE = "tasks.json"


class StateManager:
    """Owns all reads and writes for `.project` state."""

    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace.expanduser().resolve()
        self.project_dir = self.workspace / PROJECT_DIR_NAME
        self.artifacts_dir = self.project_dir / ARTIFACTS_DIR_NAME
        self.integration_dir = self.project_dir / INTEGRATION_DIR_NAME
        self.qa_dir = self.project_dir / QA_DIR_NAME
        self.qa_history_dir = self.qa_dir / QA_HISTORY_DIR_NAME
        self.repair_dir = self.project_dir / REPAIR_DIR_NAME
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
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

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

    def list_artifacts(self) -> list[Artifact]:
        """List all persisted artifacts."""

        if not self.artifacts_dir.exists():
            return []

        artifacts: list[Artifact] = []
        for path in self.artifacts_dir.glob("*.json"):
            try:
                artifact = self._load_model(path, Artifact)
                artifacts.append(artifact)
            except (ProjectStateValidationError, ProjectNotInitializedError):
                continue
        return sorted(artifacts, key=lambda a: a.generated_at, reverse=True)

    def load_artifact(self, artifact_id: str) -> Artifact | None:
        """Load a specific artifact by ID."""

        # Search for the artifact file. Since we support versioning,
        # there might be multiple files with the same base ID but different versions.
        # For now, let's assume the filename matches the ID exactly if we use unique IDs.
        # Or we can search through the directory.
        for path in self.artifacts_dir.glob(f"{artifact_id}.json"):
            return self._load_model(path, Artifact)
        return None

    def save_artifact(self, artifact: Artifact) -> None:
        """Validate and persist an artifact."""

        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = self.artifacts_dir / f"{artifact.id}.json"
        self._write_model(artifact_path, Artifact.model_validate(artifact))

    def get_next_artifact_version(self, task_id: str) -> int:
        """Determine the next version number for a task's artifacts."""

        existing = [a for a in self.list_artifacts() if a.task_id == task_id]
        if not existing:
            return 1
        return max(a.version for a in existing) + 1

    # Integration Management

    def save_integrated_package(self, package: IntegratedPackage) -> None:
        """Save the integrated package."""
        path = self.integration_dir / "integrated_package.json"
        self._write_model(path, package)

    def load_integrated_package(self) -> IntegratedPackage:
        """Load the integrated package."""
        path = self.integration_dir / "integrated_package.json"
        if not path.exists():
            msg = "Integrated package not found. Run 'omnix integrate' first."
            raise ProjectNotInitializedError(msg)
        return self._load_model(path, IntegratedPackage)

    def save_dependency_graph(self, graph: DependencyGraph) -> None:
        """Save the dependency graph."""
        path = self.integration_dir / "dependency_graph.json"
        self._write_model(path, graph)

    def load_dependency_graph(self) -> DependencyGraph:
        """Load the dependency graph."""
        path = self.integration_dir / "dependency_graph.json"
        if not path.exists():
            msg = "Dependency graph not found. Run 'omnix integrate' first."
            raise ProjectNotInitializedError(msg)
        return self._load_model(path, DependencyGraph)

    def save_integration_report(self, report: IntegrationReport) -> None:
        """Save the integration report."""
        path = self.integration_dir / "integration_report.json"
        self._write_model(path, report)

    def load_integration_report(self) -> IntegrationReport:
        """Load the integration report."""
        path = self.integration_dir / "integration_report.json"
        if not path.exists():
            msg = "Integration report not found. Run 'omnix integrate' first."
            raise ProjectNotInitializedError(msg)
        return self._load_model(path, IntegrationReport)

    def save_conflict_report(self, report: ConflictReport) -> None:
        """Save the conflict report."""
        path = self.integration_dir / "conflict_report.json"
        self._write_model(path, report)

    def load_conflict_report(self) -> ConflictReport:
        """Load the conflict report."""
        path = self.integration_dir / "conflict_report.json"
        if not path.exists():
            msg = "Conflict report not found. Run 'omnix integrate' first."
            raise ProjectNotInitializedError(msg)
        return self._load_model(path, ConflictReport)

    # QA Management

    def get_next_qa_version(self) -> int:
        """Determine the next version number for QA reports."""

        if not self.qa_history_dir.exists():
            return 1

        versions = []
        for path in self.qa_history_dir.glob("qa_summary.v*.json"):
            try:
                # Extract version from filename like qa_summary.v1.json
                parts = path.name.split(".")
                if len(parts) >= 2 and parts[1].startswith("v"):
                    versions.append(int(parts[1][1:]))
            except (ValueError, IndexError):
                continue

        return max(versions) + 1 if versions else 1

    def save_qa_reports(
        self,
        summary: QASummary,
        quality: QualityReport,
        coverage: CoverageReport,
        gap: GapReport,
        risk: RiskReport,
    ) -> None:
        """Save latest QA reports and archive them to history."""

        self.qa_dir.mkdir(parents=True, exist_ok=True)
        self.qa_history_dir.mkdir(parents=True, exist_ok=True)

        version = summary.version

        # Save latest
        self._write_model(self.qa_dir / "qa_summary.json", summary)
        self._write_model(self.qa_dir / "quality_report.json", quality)
        self._write_model(self.qa_dir / "coverage_report.json", coverage)
        self._write_model(self.qa_dir / "gap_report.json", gap)
        self._write_model(self.qa_dir / "risk_report.json", risk)

        # Save to history
        self._write_model(self.qa_history_dir / f"qa_summary.v{version}.json", summary)
        self._write_model(self.qa_history_dir / f"quality_report.v{version}.json", quality)
        self._write_model(self.qa_history_dir / f"coverage_report.v{version}.json", coverage)
        self._write_model(self.qa_history_dir / f"gap_report.v{version}.json", gap)
        self._write_model(self.qa_history_dir / f"risk_report.v{version}.json", risk)

    def load_qa_summary(self) -> QASummary:
        """Load the latest QA summary."""
        path = self.qa_dir / "qa_summary.json"
        if not path.exists():
            msg = "QA summary not found. Run 'omnix qa' first."
            raise ProjectNotInitializedError(msg)
        return self._load_model(path, QASummary)

    def load_quality_report(self) -> QualityReport:
        """Load the latest quality report."""
        path = self.qa_dir / "quality_report.json"
        if not path.exists():
            msg = "Quality report not found. Run 'omnix qa' first."
            raise ProjectNotInitializedError(msg)
        return self._load_model(path, QualityReport)

    def load_coverage_report(self) -> CoverageReport:
        """Load the latest coverage report."""
        path = self.qa_dir / "coverage_report.json"
        if not path.exists():
            msg = "Coverage report not found. Run 'omnix qa' first."
            raise ProjectNotInitializedError(msg)
        return self._load_model(path, CoverageReport)

    def load_gap_report(self) -> GapReport:
        """Load the latest gap report."""
        path = self.qa_dir / "gap_report.json"
        if not path.exists():
            msg = "Gap report not found. Run 'omnix qa' first."
            raise ProjectNotInitializedError(msg)
        return self._load_model(path, GapReport)

    def load_risk_report(self) -> RiskReport:
        """Load the latest risk report."""
        path = self.qa_dir / "risk_report.json"
        if not path.exists():
            msg = "Risk report not found. Run 'omnix qa' first."
            raise ProjectNotInitializedError(msg)
        return self._load_model(path, RiskReport)

    # Repair Management

    def save_repair_plan(self, plan: RepairPlan) -> None:
        """Persist the repair plan for the current cycle (and archive it)."""
        self.repair_dir.mkdir(parents=True, exist_ok=True)
        self._write_model(self.repair_dir / "repair_plan.json", plan)
        self._write_model(
            self.repair_dir / f"repair_plan.cycle{plan.cycle}.json", plan
        )

    def load_repair_plan(self) -> RepairPlan:
        """Load the latest repair plan."""
        path = self.repair_dir / "repair_plan.json"
        if not path.exists():
            msg = "Repair plan not found. Run 'omnix repair' first."
            raise ProjectNotInitializedError(msg)
        return self._load_model(path, RepairPlan)

    def save_repair_artifact(self, artifact: RepairArtifact) -> None:
        """Persist a repair artifact."""
        self.repair_dir.mkdir(parents=True, exist_ok=True)
        self._write_model(self.repair_dir / f"{artifact.id}.json", artifact)

    def list_repair_artifacts(self) -> list[RepairArtifact]:
        """List all persisted repair artifacts."""
        if not self.repair_dir.exists():
            return []
        artifacts: list[RepairArtifact] = []
        for path in self.repair_dir.glob("repair_artifact_*.json"):
            try:
                artifacts.append(self._load_model(path, RepairArtifact))
            except (ProjectStateValidationError, ProjectNotInitializedError):
                continue
        return sorted(artifacts, key=lambda a: (a.cycle, a.id))

    def save_repair_report(self, report: RepairReport) -> None:
        """Persist the repair report for the current cycle (and archive it)."""
        self.repair_dir.mkdir(parents=True, exist_ok=True)
        self._write_model(self.repair_dir / "repair_report.json", report)
        self._write_model(
            self.repair_dir / f"repair_report.cycle{report.cycle}.json", report
        )

    def load_repair_report(self) -> RepairReport:
        """Load the latest repair report."""
        path = self.repair_dir / "repair_report.json"
        if not path.exists():
            msg = "Repair report not found. Run 'omnix repair' first."
            raise ProjectNotInitializedError(msg)
        return self._load_model(path, RepairReport)

    def save_repair_history(self, history: RepairHistory) -> None:
        """Persist the repair cycle history — never overwrites, always appends."""
        self.repair_dir.mkdir(parents=True, exist_ok=True)
        self._write_model(self.repair_dir / "repair_history.json", history)

    def load_repair_history(self) -> RepairHistory:
        """Load the full repair history."""
        path = self.repair_dir / "repair_history.json"
        if not path.exists():
            msg = "Repair history not found. Run 'omnix repair' first."
            raise ProjectNotInitializedError(msg)
        return self._load_model(path, RepairHistory)

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
