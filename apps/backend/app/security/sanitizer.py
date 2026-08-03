"""app/security/sanitizer.py

Utilities for sanitizing outputs to prevent prompt or tool injection.
Provides simple HTML escaping and removal of dangerous patterns.
"""

import html
import re
from typing import Any, Union

# Simple patterns for dangerous content (example placeholders)
_DANGEROUS_PATTERNS = [
    r"<script.*?>.*?</script>",
    r"\bDROP\s+TABLE\b",
    r"\bDELETE\s+FROM\b",
]


def sanitize_text(text: str) -> str:
    """Escape HTML and strip dangerous patterns from a plain string."""
    escaped = html.escape(text)
    for pattern in _DANGEROUS_PATTERNS:
        escaped = re.sub(pattern, "", escaped, flags=re.IGNORECASE | re.DOTALL)
    return escaped


def sanitize_payload(payload: Union[dict, list, str]) -> Union[dict, list, str]:
    """Recursively sanitize JSON‑compatible payloads."""
    if isinstance(payload, dict):
        return {k: sanitize_payload(v) for k, v in payload.items()}
    if isinstance(payload, list):
        return [sanitize_payload(item) for item in payload]
    if isinstance(payload, str):
        return sanitize_text(payload)
    return payload
