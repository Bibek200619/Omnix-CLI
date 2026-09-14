"""Pydantic schemas for the Omnix CLI."""

from omnix_cli.schemas.blueprint import (
    ArchitectureNote,
    EntityDefinition,
    FeatureDefinition,
    GoalDefinition,
    ModuleDefinition,
    PageDefinition,
    ProjectBlueprint,
)
from omnix_cli.schemas.build import (
    BuildConfig,
    BuildHistory,
    BuildReport,
    BuildStatus,
    FinalProjectPackage,
)
from omnix_cli.schemas.memory import ProjectMemory
from omnix_cli.schemas.models import ModelsConfig
from omnix_cli.schemas.tasks import (
    AgentRole,
    TaskAssignedAgent,
    TaskDefinition,
    TaskPlan,
    TaskPriority,
    TaskStatus,
)

__all__ = [
    "AgentRole",
    "ArchitectureNote",
    "BuildConfig",
    "BuildHistory",
    "BuildReport",
    "BuildStatus",
    "EntityDefinition",
    "FeatureDefinition",
    "FinalProjectPackage",
    "GoalDefinition",
    "ModelsConfig",
    "ModuleDefinition",
    "PageDefinition",
    "ProjectBlueprint",
    "ProjectMemory",
    "TaskAssignedAgent",
    "TaskDefinition",
    "TaskPlan",
    "TaskPriority",
    "TaskStatus",
]
