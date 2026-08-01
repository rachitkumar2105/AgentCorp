"""
Audit log repository forwarding wrapper.
"""

from app.repositories.audit_repository import AuditRepository

# Expose AuditLogRepository pointing to AuditRepository for backward compatibility
AuditLogRepository = AuditRepository
