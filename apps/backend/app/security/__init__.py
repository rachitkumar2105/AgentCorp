"""app/security/__init__.py

Security package public surface.
"""

from app.security.authorization import has_permission
from app.security.encryption import encrypt, decrypt
from app.security.pii import detect_pii, redact_pii
from app.security.sanitizer import sanitize_text, sanitize_payload
from app.security.rate_limiter import is_rate_limited
from app.security.exceptions import (
    SecurityError,
    AuthenticationError,
    AuthorizationError,
    PolicyViolationError,
    RateLimitExceededError,
    QuotaExceededError,
    ComplianceError,
)

__all__ = [
    "has_permission",
    "encrypt",
    "decrypt",
    "detect_pii",
    "redact_pii",
    "sanitize_text",
    "sanitize_payload",
    "is_rate_limited",
    "SecurityError",
    "AuthenticationError",
    "AuthorizationError",
    "PolicyViolationError",
    "RateLimitExceededError",
    "QuotaExceededError",
    "ComplianceError",
]
