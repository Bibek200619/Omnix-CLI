"""Domain exceptions for the CLI."""

from __future__ import annotations


class OmnixError(Exception):
    """Base class for expected CLI errors."""


class CommandUsageError(OmnixError):
    """Raised when command arguments are syntactically valid but unsupported."""


class ProjectAlreadyInitializedError(OmnixError):
    """Raised when `.project` state already exists."""


class ProjectNotInitializedError(OmnixError):
    """Raised when a command requires initialized project state."""


class ProjectStateValidationError(OmnixError):
    """Raised when persisted project state fails schema validation."""


class BlueprintValidationError(OmnixError):
    """Raised when an architecture blueprint is incomplete or invalid."""
