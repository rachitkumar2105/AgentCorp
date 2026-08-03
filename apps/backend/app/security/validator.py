"""app/security/validator.py

Utility functions for validating incoming request data.

Provides:
  - Generic payload validation via Pydantic models
  - Prompt injection detection
  - Tool call security checks
  - Field length guards
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Type, TypeVar

from pydantic import BaseModel, ValidationError

M = TypeVar("M", bound=BaseModel)

# ---------------------------------------------------------------------------
# Prompt injection patterns
# ---------------------------------------------------------------------------
_PROMPT_INJECTION_PATTERNS: List[str] = [
    r"ignore\s+(previous|all|above)\s+instructions",
    r"disregard\s+(all|previous|your)\s+instructions",
    r"you\s+are\s+now\s+(?:a|an|the)\s+\w+",
    r"forget\s+(everything|all)\s+(you\s+know|previously)",
    r"jailbreak",
    r"dan\s+mode",
    r"do\s+anything\s+now",
    r"act\s+as\s+(?:if\s+you\s+have\s+no\s+restrictions|root)",
    r"system\s*:\s*(ignore|override|bypass)",
    r"<\s*system\s*>",
]

_INJECTION_RE = re.compile(
    "|".join(_PROMPT_INJECTION_PATTERNS),
    re.IGNORECASE | re.DOTALL,
)

# ---------------------------------------------------------------------------
# Tool security patterns (block attempts to call dangerous shell commands)
# ---------------------------------------------------------------------------
_DANGEROUS_TOOL_PATTERNS: List[str] = [
    r"\brm\s+-rf\b",
    r"\bsudo\b",
    r"\bchmod\s+777\b",
    r"\b(?:curl|wget)\s+.*\s*\|\s*(?:sh|bash)\b",
    r"\beval\s*\(",
    r"\bos\.system\b",
    r"\bsubprocess\.(?:call|run|Popen)\b",
]

_TOOL_RE = re.compile(
    "|".join(_DANGEROUS_TOOL_PATTERNS),
    re.IGNORECASE | re.DOTALL,
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate_payload(model: Type[M], payload: Dict[str, Any]) -> M:
    """Validate a JSON payload against a Pydantic model.

    Args:
        model: Pydantic model class.
        payload: Raw dict to validate.

    Returns:
        A validated Pydantic model instance.

    Raises:
        ValidationError: If the payload does not conform to the model.
    """
    return model(**payload)


def ensure_max_length(value: str, max_length: int, field_name: str = "field") -> None:
    """Raise ``ValueError`` if *value* exceeds *max_length* characters."""
    if len(value) > max_length:
        raise ValueError(
            f"'{field_name}' exceeds maximum length of {max_length} characters "
            f"(got {len(value)})."
        )


def detect_prompt_injection(text: str) -> bool:
    """Return ``True`` if *text* contains prompt injection patterns."""
    return bool(_INJECTION_RE.search(text))


def assert_no_prompt_injection(text: str, field_name: str = "input") -> None:
    """Raise ``ValueError`` if *text* contains prompt injection patterns.

    Args:
        text: The user-supplied text to scan.
        field_name: Label used in the error message.

    Raises:
        ValueError: When injection is detected.
    """
    if detect_prompt_injection(text):
        raise ValueError(
            f"Potential prompt injection detected in '{field_name}'."
        )


def detect_dangerous_tool_call(text: str) -> bool:
    """Return ``True`` if *text* appears to contain dangerous tool/shell commands."""
    return bool(_TOOL_RE.search(text))


def assert_safe_tool_call(text: str, field_name: str = "tool_call") -> None:
    """Raise ``ValueError`` if *text* contains dangerous patterns.

    Args:
        text: Tool call content to scan.
        field_name: Label used in the error message.

    Raises:
        ValueError: When dangerous content is detected.
    """
    if detect_dangerous_tool_call(text):
        raise ValueError(
            f"Dangerous tool call pattern detected in '{field_name}'."
        )
