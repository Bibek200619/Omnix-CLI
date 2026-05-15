"""Typed provider-layer exceptions."""

from __future__ import annotations

from aicli.core.exceptions import AicliError


class ProviderError(AicliError):
    """Base class for provider-layer failures."""


class ProviderAuthenticationError(ProviderError):
    """Raised when a provider cannot authenticate a request."""


class ProviderConfigurationError(ProviderError):
    """Raised when provider configuration is invalid or incomplete."""


class ProviderRequestError(ProviderError):
    """Raised when a provider request fails after configuration is valid."""
