"""Blueprint completeness validation for Phase 3 architecture workflows."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from omnix_cli.core.exceptions import BlueprintValidationError
from omnix_cli.schemas.blueprint import ProjectBlueprint


class BlueprintValidationResult(BaseModel):
    """Structured result for architecture blueprint validation."""

    model_config = ConfigDict(extra="forbid")

    valid: bool
    errors: list[str] = Field(default_factory=list)


def collect_blueprint_validation_errors(blueprint: ProjectBlueprint) -> list[str]:
    """Return clear validation errors for a complete architecture blueprint."""

    errors: list[str] = []
    if not blueprint.project_name.strip():
        errors.append("project_name is required.")
    if not blueprint.features:
        errors.append("at least one feature is required.")
    if not blueprint.entities:
        errors.append("at least one entity is required.")
    if not blueprint.modules:
        errors.append("at least one module is required.")
    if not blueprint.architecture_notes:
        errors.append("at least one architecture note is required.")
    return errors


def validate_architecture_blueprint(
    blueprint: ProjectBlueprint,
) -> BlueprintValidationResult:
    """Validate that a blueprint is complete enough to become source of truth."""

    errors = collect_blueprint_validation_errors(blueprint)
    result = BlueprintValidationResult(valid=not errors, errors=errors)
    if errors:
        formatted_errors = "\n".join(f"- {error}" for error in errors)
        msg = f"Invalid architecture blueprint:\n{formatted_errors}"
        raise BlueprintValidationError(msg)
    return result
