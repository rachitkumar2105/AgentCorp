"""Unit tests for runtime production validation."""

from __future__ import annotations

from app.config.settings import Settings
from app.runtime.validation import validate_runtime_configuration


def test_runtime_configuration_validation_rejects_default_secret_and_provider() -> None:
    settings = Settings(
        SECRET_KEY="changeme-secret",
        DEFAULT_PROVIDER="missing-provider",
        GROQ_API_KEY="",
        OPENAI_API_KEY="",
        ANTHROPIC_API_KEY="",
        GEMINI_API_KEY="",
        OPENROUTER_API_KEY="",
        OLLAMA_BASE_URL="",
    )

    report = validate_runtime_configuration(settings)

    assert report.valid is False
    assert any(issue.field == "SECRET_KEY" for issue in report.issues)
    assert any(issue.field == "DEFAULT_PROVIDER" for issue in report.issues)


def test_runtime_configuration_validation_accepts_supported_settings() -> None:
    settings = Settings(
        SECRET_KEY="secure-production-secret",
        DEFAULT_PROVIDER="groq",
        GROQ_API_KEY="key",
        OLLAMA_BASE_URL="http://localhost:11434",
    )

    report = validate_runtime_configuration(settings)

    assert report.valid is True
    assert report.issues == ()
