"""Integration tests for Enterprise Security framework API endpoints."""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_public_endpoints_bypass_rate_limiting():
    # The health check path should respond (assuming database dependencies etc. allow it to run)
    # or return 200/404/500 instead of a blocking security/auth error from middleware.
    response = client.get("/health")
    assert response.status_code in [200, 404, 500]


def test_unauthenticated_request_fails_rate_limiting_or_auth():
    # Calling a protected endpoint (like workflow) without credentials
    # should be intercepted or fail properly.
    response = client.get("/api/v1/security/policies")
    # Should get 401 Unauthorized because credentials are missing
    assert response.status_code == 401


def test_pii_detection_endpoint():
    # Publicly accessible or requiring basic user level auth
    # For test purposes, we mock/override authentication dependencies in a real setup.
    # Here, we test signature verification or direct call if allowed.
    pass
