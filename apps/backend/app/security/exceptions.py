"""app/security/exceptions.py

Custom exception hierarchy for the security package.
All exceptions inherit from `Exception` so they can be caught by the global
exception handler defined in `app.exceptions.handlers`.
"""

class SecurityError(Exception):
    """Base class for all security‑related errors."""
    pass

class AuthenticationError(SecurityError):
    """Raised when authentication fails or is missing."""
    pass

class AuthorizationError(SecurityError):
    """Raised when a user lacks the required permission."""
    pass

class PolicyViolationError(SecurityError):
    """Raised when a request violates an active security policy."""
    pass

class RateLimitExceededError(SecurityError):
    """Raised when the request exceeds the allowed rate limit."""
    pass

class QuotaExceededError(SecurityError):
    """Raised when the request would exceed the allocated quota."""
    pass

class ComplianceError(SecurityError):
    """Raised for compliance‑related failures (e.g., GDPR export denial)."""
    pass
