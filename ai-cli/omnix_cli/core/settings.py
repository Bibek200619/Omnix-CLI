"""Runtime settings loaded from environment variables and `.env`."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application settings.

    Secrets are intentionally loaded from the environment instead of project
    state files so `.project` remains safe to commit.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    google_api_key: str | None = None
    openrouter_api_key: str | None = None
    deepseek_api_key: str | None = None

    openai_base_url: str = "https://api.openai.com/v1"
    provider_timeout_seconds: float = Field(default=30.0, gt=0)
