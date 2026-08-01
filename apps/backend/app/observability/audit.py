"""
Audit logging interface.
"""

from typing import Any, Dict, Optional
from app.observability.logging import get_logger, get_logging_context

logger = get_logger(__name__)


class AuditLogger:
    """Helper class to dispatch structured audit log events."""

    def __init__(self):
        self._handlers = []

    def register_handler(self, handler) -> None:
        """Register a handler (e.g. database saver) for audit events."""
        self._handlers.append(handler)

    async def log(
        self,
        action: str,
        resource: str,
        resource_id: Optional[str] = None,
        actor_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
        status: str = "success",
        ip_address: Optional[str] = None,
    ) -> None:
        """Log an audit event."""
        ctx = get_logging_context()
        org_id = organization_id or ctx.get("organization_id")
        user_id = actor_id or ctx.get("user_id")

        event = {
            "action": action,
            "resource": resource,
            "resource_id": resource_id,
            "actor_id": user_id,
            "organization_id": org_id,
            "extra_metadata": extra_metadata or {},
            "status": status,
            "ip_address": ip_address,
        }

        # Log it via structured logger
        logger.info(
            "Audit event emitted: %s on %s:%s by actor:%s",
            action,
            resource,
            resource_id,
            user_id,
            extra={"audit_event": event}
        )

        # Dispatch to handlers (e.g. Database Repository handler)
        for handler in self._handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error("Audit handler failed to process event: %s", str(e))


# Global audit logger instance
audit_logger = AuditLogger()
