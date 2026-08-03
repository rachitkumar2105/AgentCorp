"""app/security/policy_engine.py

Policy engine: stores, evaluates and caches security policies.

Policy DSL (stored in ``SecurityPolicy.condition`` JSON field):
  {
    "user_role": "admin",          # optional – must match user.role
    "org_id":    42,               # optional – must match organization.id
    "time_from": "09:00",          # optional – UTC hour:minute lower bound
    "time_until": "18:00",         # optional – UTC hour:minute upper bound
    "allowed_ips": ["1.2.3.0/24"] # optional – CIDR list (requires client IP)
  }

All fields are optional; an empty condition dict passes unconditionally.
"""
from __future__ import annotations

import ipaddress
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.security.constants import ALLOW, DENY, CONDITIONAL
from app.security.exceptions import PolicyViolationError


# ---------------------------------------------------------------------------
# In-process policy cache (TTL = 60 s)
# ---------------------------------------------------------------------------

_cache_lock = threading.Lock()
_policy_cache: List[Any] = []
_cache_loaded_at: float = 0.0
_CACHE_TTL_SECONDS = 60


def _load_policies(db) -> List[Any]:
    """Load active policies from the database, with a 60-second cache."""
    import time

    global _policy_cache, _cache_loaded_at

    now = time.time()
    with _cache_lock:
        if now - _cache_loaded_at > _CACHE_TTL_SECONDS:
            from app.models.security_policy import SecurityPolicy
            _policy_cache = db.query(SecurityPolicy).filter_by(is_active=True).all()
            _cache_loaded_at = now
        return list(_policy_cache)


def invalidate_policy_cache() -> None:
    """Force the next call to reload policies from the database."""
    global _cache_loaded_at
    with _cache_lock:
        _cache_loaded_at = 0.0


# ---------------------------------------------------------------------------
# Condition evaluators
# ---------------------------------------------------------------------------

def _check_time(condition: Dict) -> bool:
    """Enforce time-based access windows (UTC)."""
    from_str = condition.get("time_from")
    until_str = condition.get("time_until")
    if not from_str and not until_str:
        return True

    now = datetime.now(timezone.utc)
    current_hm = now.strftime("%H:%M")

    if from_str and current_hm < from_str:
        return False
    if until_str and current_hm > until_str:
        return False
    return True


def _check_ip(condition: Dict, client_ip: Optional[str]) -> bool:
    """Check that client_ip falls within one of the allowed CIDR ranges."""
    allowed = condition.get("allowed_ips")
    if not allowed:
        return True
    if not client_ip:
        return False
    try:
        addr = ipaddress.ip_address(client_ip)
        return any(addr in ipaddress.ip_network(cidr, strict=False) for cidr in allowed)
    except ValueError:
        return False


def _evaluate_condition(
    condition: Optional[Dict],
    user: Any,
    organization: Any,
    client_ip: Optional[str],
) -> bool:
    """Return True if all conditions in the policy condition dict are satisfied."""
    if not condition:
        return True

    # Role check
    required_role = condition.get("user_role")
    if required_role and getattr(user, "role", None) != required_role:
        return False

    # Organization check
    required_org = condition.get("org_id")
    if required_org is not None and getattr(organization, "id", None) != required_org:
        return False

    # Time window
    if not _check_time(condition):
        return False

    # IP allowlist
    if not _check_ip(condition, client_ip):
        return False

    return True


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def evaluate_policies(
    db,
    user: Any,
    organization: Any,
    resource: str,
    action: str,
    client_ip: Optional[str] = None,
) -> bool:
    """Evaluate all active policies for the given request context.

    Args:
        db: SQLAlchemy session used to load policies.
        user: Authenticated user model instance.
        organization: Organization model instance.
        resource: Resource string, e.g. ``"security:policy"``.
        action: Action string, e.g. ``"read"`` or ``"write"``.
        client_ip: Optional client IP address for IP-allowlist checks.

    Returns:
        ``True`` if the request is explicitly *allowed* by a matching policy.

    Raises:
        PolicyViolationError: If a DENY policy matches.
    """
    policies = _load_policies(db)

    for policy in policies:
        if not policy.matches(user, organization, resource, action):
            continue

        if policy.effect == DENY:
            raise PolicyViolationError(
                f"Policy '{policy.name}' denies {action} on {resource}."
            )

        if policy.effect == ALLOW:
            return True

        if policy.effect == CONDITIONAL:
            if _evaluate_condition(policy.condition, user, organization, client_ip):
                return True

    # Default: deny if no matching ALLOW/CONDITIONAL policy found
    return False
