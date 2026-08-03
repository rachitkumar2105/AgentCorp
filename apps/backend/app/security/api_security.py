"""app/security/api_security.py

Utilities for securing FastAPI endpoints. Includes CSP header injection and request signature validation placeholders.
"""

from fastapi import Request, Response


def add_security_headers(response: Response) -> None:
    """Inject common security headers into the response.

    - Content Security Policy (CSP)
    - X-Content-Type-Options
    - X-Frame-Options
    - Referrer-Policy
    """
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"


async def verify_request_signature(request: Request) -> bool:
    """Placeholder for request signature verification (e.g., HMAC).
    Returns True if the signature is valid, False otherwise.
    """
    # Implementation can be added later – for now always accept.
    return True
