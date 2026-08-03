"""app/security/pii.py

PII detection, masking, and redaction utilities.

Supported PII types (regex-based):
  - email
  - phone (international formats)
  - credit_card
  - ssn (US)
  - ip_address (IPv4)
  - date_of_birth (common date formats)
  - street_address

For production workloads consider integrating spaCy NER or AWS Comprehend
as a complement to the regex layer.
"""
from __future__ import annotations

import re
from typing import Dict, List

# ---------------------------------------------------------------------------
# Pattern registry
# ---------------------------------------------------------------------------

_PII_PATTERNS: Dict[str, str] = {
    "email": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
    "phone": r"\+?[\d\s\-().]{7,15}\d",
    "credit_card": r"\b(?:\d[ -]?){13,16}\b",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "ip_address": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    "date_of_birth": (
        r"\b(?:\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}|"
        r"\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2})\b"
    ),
    "street_address": (
        r"\d+\s+[A-Za-z0-9]+(?:\s+[A-Za-z0-9]+)*"
        r"\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct)"
    ),
}

_COMPILED: Dict[str, re.Pattern] = {
    name: re.compile(pattern, re.IGNORECASE)
    for name, pattern in _PII_PATTERNS.items()
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_pii(text: str) -> List[Dict[str, str]]:
    """Return a list of detected PII elements with ``type``, ``value``, and ``start``/``end`` offsets.

    Args:
        text: Plain-text string to scan.

    Returns:
        List of dicts with keys ``type``, ``value``, ``start``, ``end``.
    """
    detections: List[Dict[str, str]] = []
    for pii_type, pattern in _COMPILED.items():
        for match in pattern.finditer(text):
            detections.append(
                {
                    "type": pii_type,
                    "value": match.group(),
                    "start": str(match.start()),
                    "end": str(match.end()),
                }
            )
    return detections


def mask_pii(text: str, pii_types: List[str] | None = None, mask_char: str = "*") -> str:
    """Replace PII values with a character mask (preserves length).

    Args:
        text: Input string.
        pii_types: Restrict masking to these PII types. ``None`` = all types.
        mask_char: Character used for masking.
    """
    types = set(pii_types) if pii_types else set(_COMPILED.keys())
    for pii_type, pattern in _COMPILED.items():
        if pii_type not in types:
            continue
        text = pattern.sub(
            lambda m: mask_char * len(m.group()),
            text,
        )
    return text


def redact_pii(text: str, pii_types: List[str] | None = None, replacement: str = "[REDACTED]") -> str:
    """Replace PII values with *replacement* token.

    Args:
        text: Input string.
        pii_types: Restrict redaction to these PII types. ``None`` = all types.
        replacement: Replacement token.
    """
    types = set(pii_types) if pii_types else set(_COMPILED.keys())
    for pii_type, pattern in _COMPILED.items():
        if pii_type not in types:
            continue
        text = pattern.sub(replacement, text)
    return text


def contains_pii(text: str) -> bool:
    """Return ``True`` if *text* contains any detectable PII."""
    return bool(detect_pii(text))
