from __future__ import annotations

from aicli.core.settings import Settings


def test_settings_load_api_keys_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "openai-test-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-test-key")
    monkeypatch.setenv("GOOGLE_API_KEY", "google-test-key")
    monkeypatch.setenv("OPENROUTER_API_KEY", "openrouter-test-key")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "deepseek-test-key")

    settings = Settings()

    assert settings.openai_api_key == "openai-test-key"
    assert settings.anthropic_api_key == "anthropic-test-key"
    assert settings.google_api_key == "google-test-key"
    assert settings.openrouter_api_key == "openrouter-test-key"
    assert settings.deepseek_api_key == "deepseek-test-key"


def test_settings_do_not_require_api_keys(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    settings = Settings()

    assert settings.openai_api_key is None
    assert settings.provider_timeout_seconds == 30.0
