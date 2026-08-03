"""
Deterministic runtime configuration validation for production readiness.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from app.config.settings import Settings
from app.runtime.governance import ApprovalState
from app.runtime.optimization import OptimizationPolicy


@dataclass(frozen=True)
class ValidationIssue:
    field: str
    message: str


@dataclass(frozen=True)
class ValidationReport:
    valid: bool
    issues: tuple[ValidationIssue, ...]


def validate_runtime_configuration(settings: Settings) -> ValidationReport:
    issues: list[ValidationIssue] = []

    if settings.DEFAULT_PROVIDER.lower() not in _configured_providers(settings):
        issues.append(ValidationIssue("DEFAULT_PROVIDER", f"Default provider '{settings.DEFAULT_PROVIDER}' is not configured."))

    if settings.PORT <= 0 or settings.PORT > 65535:
        issues.append(ValidationIssue("PORT", "Port must be between 1 and 65535."))

    if settings.RATE_LIMIT_MAX_REQUESTS <= 0:
        issues.append(ValidationIssue("RATE_LIMIT_MAX_REQUESTS", "Rate limit must be positive."))

    if settings.RATE_LIMIT_WINDOW_SECONDS <= 0:
        issues.append(ValidationIssue("RATE_LIMIT_WINDOW_SECONDS", "Rate limit window must be positive."))

    if settings.DATA_RETENTION_DAYS <= 0:
        issues.append(ValidationIssue("DATA_RETENTION_DAYS", "Data retention days must be positive."))

    if settings.PURGE_GRACE_DAYS < 0:
        issues.append(ValidationIssue("PURGE_GRACE_DAYS", "Purge grace days cannot be negative."))

    if not settings.SECRET_KEY or settings.SECRET_KEY == "changeme-secret":
        issues.append(ValidationIssue("SECRET_KEY", "A production SECRET_KEY must be configured."))

    if settings.DEBUG and settings.APP_VERSION:
        # Debug mode is allowed in non-production; no issue recorded.
        pass

    if not _is_supported_approval_state("auto"):
        issues.append(ValidationIssue("APPROVAL_STATE", "Approval state mapping is invalid."))

    if not _is_supported_optimization_policy("balanced"):
        issues.append(ValidationIssue("OPTIMIZATION_POLICY", "Optimization policy mapping is invalid."))

    return ValidationReport(valid=not issues, issues=tuple(issues))


def _configured_providers(settings: Settings) -> tuple[str, ...]:
    providers = []
    if settings.GROQ_API_KEY:
        providers.append("groq")
    if settings.OPENAI_API_KEY:
        providers.append("openai")
    if settings.ANTHROPIC_API_KEY:
        providers.append("anthropic")
    if settings.GEMINI_API_KEY:
        providers.append("gemini")
    if settings.OPENROUTER_API_KEY:
        providers.append("openrouter")
    if settings.OLLAMA_BASE_URL:
        providers.append("ollama")
    return tuple(providers)


def _is_supported_approval_state(state: str) -> bool:
    return state in {item.value for item in ApprovalState}


def _is_supported_optimization_policy(policy: str) -> bool:
    return policy in {item.value for item in OptimizationPolicy}
