"""
Runtime V2 enterprise governance layer.

Deterministic governance checks only. The layer supervises Runtime V2 but
never replaces it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from app.observability.audit import audit_logger
from app.observability.diagnostics import register_runtime_governance


class ApprovalState(str, Enum):
    AUTO = "auto"
    MANUAL = "manual"
    CONDITIONAL = "conditional"
    ORGANIZATION = "organization"


@dataclass(frozen=True)
class PolicyResult:
    allowed: bool
    reason: str
    policy_name: str
    policy_type: str
    details: dict[str, Any]


@dataclass(frozen=True)
class ApprovalResult:
    state: ApprovalState
    approved: bool
    reason: str
    approver: str
    details: dict[str, Any]


@dataclass(frozen=True)
class ComplianceResult:
    compliant: bool
    reason: str
    checks: tuple[str, ...]
    details: dict[str, Any]


@dataclass(frozen=True)
class ExecutionGuardResult:
    allowed: bool
    reason: str
    blocked: tuple[str, ...]
    warnings: tuple[str, ...]
    details: dict[str, Any]


@dataclass(frozen=True)
class GovernanceDecision:
    allowed: bool
    policy_result: PolicyResult
    approval_result: ApprovalResult
    compliance_result: ComplianceResult
    execution_guard_result: ExecutionGuardResult
    reason: str


@dataclass(frozen=True)
class GovernanceReport:
    policy_result: PolicyResult
    approval_result: ApprovalResult
    compliance_result: ComplianceResult
    execution_guard_result: ExecutionGuardResult
    decision: GovernanceDecision
    started_at: str
    completed_at: str
    duration: float
    trace: tuple[dict[str, Any], ...]
    persisted: bool
    metadata: dict[str, Any]


class PolicyEngine:
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {
            "allowed_providers": (),
            "disallowed_capabilities": (),
            "allowed_workflows": (),
            "allowed_tools": (),
            "cost_limit": None,
            "execution_limit": None,
        }

    def evaluate(self, *, payload: Any, user: Any, organization: Any) -> PolicyResult:
        provider = getattr(payload, "provider", None)
        tool_choice = getattr(payload, "tool_choice", None)
        if self.config.get("allowed_providers") and provider and provider not in self.config["allowed_providers"]:
            return PolicyResult(False, f"Provider '{provider}' is restricted.", "provider_restriction", "provider", {"provider": provider})
        if self.config.get("allowed_tools") and tool_choice and tool_choice not in self.config["allowed_tools"]:
            return PolicyResult(False, f"Tool '{tool_choice}' is restricted.", "tool_restriction", "tool", {"tool": tool_choice})
        if self.config.get("cost_limit") is not None and float(getattr(payload, "max_tokens", 0) or 0) > float(self.config["cost_limit"]):
            return PolicyResult(False, "Requested execution exceeds configured cost limit.", "cost_limit", "cost", {"max_tokens": getattr(payload, "max_tokens", None)})
        if self.config.get("execution_limit") is not None and float(getattr(payload, "max_tokens", 0) or 0) > float(self.config["execution_limit"]):
            return PolicyResult(False, "Requested execution exceeds configured execution limit.", "execution_limit", "execution", {"max_tokens": getattr(payload, "max_tokens", None)})
        return PolicyResult(True, "Policy evaluation passed.", "default_allow", "default", {"provider": provider, "tool_choice": tool_choice})


class ApprovalEngine:
    def decide(self, *, policy_result: PolicyResult, user: Any, organization: Any, payload: Any) -> ApprovalResult:
        if not policy_result.allowed:
            return ApprovalResult(ApprovalState.MANUAL, False, policy_result.reason, "governance", {"policy": policy_result.policy_name})
        if getattr(user, "is_superuser", False):
            return ApprovalResult(ApprovalState.AUTO, True, "Superuser auto-approved.", "system", {"user_id": getattr(user, "id", None)})
        if getattr(organization, "requires_approval", False):
            return ApprovalResult(ApprovalState.ORGANIZATION, True, "Organization approval granted by policy.", "organization", {"organization_id": getattr(organization, "id", None)})
        if getattr(payload, "temperature", None) is not None and float(getattr(payload, "temperature", 0.0)) > 1.5:
            return ApprovalResult(ApprovalState.CONDITIONAL, False, "High-risk request requires manual approval.", "governance", {"temperature": getattr(payload, "temperature", None)})
        return ApprovalResult(ApprovalState.AUTO, True, "Approved automatically.", "system", {})


class ComplianceEngine:
    def validate(self, *, user: Any, organization: Any, payload: Any) -> ComplianceResult:
        checks: list[str] = []
        if not getattr(user, "is_active", True):
            return ComplianceResult(False, "Inactive users cannot execute runtime requests.", tuple(checks), {"user_id": getattr(user, "id", None)})
        checks.append("active_user")
        if organization is None:
            return ComplianceResult(False, "Organization context is required.", tuple(checks), {"organization": None})
        checks.append("organization_context")
        if getattr(organization, "is_active", True) is False:
            return ComplianceResult(False, "Organization is inactive.", tuple(checks), {"organization_id": getattr(organization, "id", None)})
        checks.append("active_organization")
        if getattr(payload, "runtime_version", None) == "AgentCorp V1":
            return ComplianceResult(True, "V1 requests are allowed and bypass V2 governance.", tuple(checks), {"runtime_version": getattr(payload, "runtime_version", None)})
        checks.append("runtime_version")
        return ComplianceResult(True, "Compliance validation passed.", tuple(checks), {"runtime_version": getattr(payload, "runtime_version", None)})


class ExecutionGuard:
    def validate(self, *, policy_result: PolicyResult, approval_result: ApprovalResult, compliance_result: ComplianceResult, payload: Any) -> ExecutionGuardResult:
        blocked: list[str] = []
        warnings: list[str] = []
        if not policy_result.allowed:
            blocked.append("policy")
        if not approval_result.approved:
            blocked.append("approval")
        if not compliance_result.compliant:
            blocked.append("compliance")
        if getattr(payload, "provider", None) and getattr(payload, "provider") in {"forbidden", "blocked"}:
            blocked.append("provider")
        if getattr(payload, "tool_choice", None) and getattr(payload, "tool_choice") in {"forbidden", "blocked"}:
            blocked.append("tool")
        if getattr(payload, "runtime_version", None) not in {"AgentCorp V1", "AgentCorp V2"}:
            blocked.append("runtime_version")
        return ExecutionGuardResult(
            allowed=not blocked,
            reason="Execution guard passed." if not blocked else "Execution blocked by governance guard.",
            blocked=tuple(blocked),
            warnings=tuple(warnings),
            details={"provider": getattr(payload, "provider", None), "tool_choice": getattr(payload, "tool_choice", None)},
        )


class GovernanceEngine:
    def __init__(
        self,
        *,
        policy_engine: PolicyEngine | None = None,
        approval_engine: ApprovalEngine | None = None,
        compliance_engine: ComplianceEngine | None = None,
        execution_guard: ExecutionGuard | None = None,
    ) -> None:
        self.policy_engine = policy_engine or PolicyEngine()
        self.approval_engine = approval_engine or ApprovalEngine()
        self.compliance_engine = compliance_engine or ComplianceEngine()
        self.execution_guard = execution_guard or ExecutionGuard()

    async def govern(self, *, payload: Any, user: Any, organization: Any, affected_runtime: str) -> GovernanceReport:
        started_at = datetime.now(timezone.utc)
        policy_result = self.policy_engine.evaluate(payload=payload, user=user, organization=organization)
        approval_result = self.approval_engine.decide(policy_result=policy_result, user=user, organization=organization, payload=payload)
        compliance_result = self.compliance_engine.validate(user=user, organization=organization, payload=payload)
        execution_guard_result = self.execution_guard.validate(
            policy_result=policy_result,
            approval_result=approval_result,
            compliance_result=compliance_result,
            payload=payload,
        )
        decision = GovernanceDecision(
            allowed=policy_result.allowed and approval_result.approved and compliance_result.compliant and execution_guard_result.allowed,
            policy_result=policy_result,
            approval_result=approval_result,
            compliance_result=compliance_result,
            execution_guard_result=execution_guard_result,
            reason="Governance approved execution." if policy_result.allowed and approval_result.approved and compliance_result.compliant and execution_guard_result.allowed else "Governance blocked execution.",
        )
        completed_at = datetime.now(timezone.utc)
        report = GovernanceReport(
            policy_result=policy_result,
            approval_result=approval_result,
            compliance_result=compliance_result,
            execution_guard_result=execution_guard_result,
            decision=decision,
            started_at=started_at.isoformat(),
            completed_at=completed_at.isoformat(),
            duration=(completed_at - started_at).total_seconds(),
            trace=(
                {"stage_name": "Governance Started", "status": "COMPLETED", "summary": "Governance analysis started."},
                {"stage_name": "Policy Validation", "status": "COMPLETED", "summary": policy_result.reason},
                {"stage_name": "Approval Validation", "status": "COMPLETED", "summary": approval_result.reason},
                {"stage_name": "Compliance Validation", "status": "COMPLETED", "summary": compliance_result.reason},
                {"stage_name": "Execution Guard", "status": "COMPLETED", "summary": execution_guard_result.reason},
                {"stage_name": "Governance Completed", "status": "COMPLETED", "summary": decision.reason},
            ),
            persisted=True,
            metadata={"affected_runtime": affected_runtime, "policy_name": policy_result.policy_name, "approval_state": approval_result.state.value},
        )
        await audit_logger.log(
            action="governance_evaluated",
            resource="runtime",
            resource_id=affected_runtime,
            actor_id=getattr(user, "id", None),
            organization_id=getattr(organization, "id", None),
            status="success" if decision.allowed else "blocked",
            extra_metadata={
                "decision": decision.allowed,
                "reason": decision.reason,
                "policy": policy_result.policy_name,
                "approval_state": approval_result.state.value,
                "compliance": compliance_result.compliant,
                "blocked": list(execution_guard_result.blocked),
            },
        )
        await register_runtime_governance(
            str(getattr(organization, "id", "runtime")),
            {
                "affected_runtime": affected_runtime,
                "decision": decision.allowed,
                "policy_result": policy_result.__dict__,
                "approval_result": approval_result.__dict__,
                "compliance_result": compliance_result.__dict__,
                "execution_guard_result": execution_guard_result.__dict__,
                "trace": [entry for entry in report.trace],
                "reason": decision.reason,
            },
        )
        return report
