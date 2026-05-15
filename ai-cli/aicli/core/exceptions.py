"""Domain exceptions for the CLI."""

from __future__ import annotations


class AicliError(Exception):
    """Base class for expected CLI errors."""


class CommandUsageError(AicliError):
    """Raised when command arguments are syntactically valid but unsupported."""


class ProjectAlreadyInitializedError(AicliError):
    """Raised when `.project` state already exists."""


class ProjectNotInitializedError(AicliError):
    """Raised when a command requires initialized project state."""


class ProjectStateValidationError(AicliError):
    """Raised when persisted project state fails schema validation."""
