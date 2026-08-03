"""Unit tests for runtime governance."""

from __future__ import annotations

import asyncio

from app.runtime.governance import ApprovalState, GovernanceEngine, PolicyEngine
from app.services.observability_service import ObservabilityService


class _User:
    def __init__(self, user_id: int = 7, is_active: bool = True, is_superuser: bool = False):
        self.id = user_id
        self.is_active = is_active
        self.is_superuser = is_superuser


class _Org:
    def __init__(self, org_id: int = 11, is_active: bool = True, requires_approval: bool = False):
        self.id = org_id
        self.is_active = is_active
        self.requires_approval = requires_approval


class _Payload:
    def __init__(self, runtime_version: str = "AgentCorp V2", provider: str | None = None, tool_choice: str | None = None, temperature: float | None = None, max_tokens: int | None = None):
        self.runtime_version = runtime_version
        self.provider = provider
        self.tool_choice = tool_choice
        self.temperature = temperature
        self.max_tokens = max_tokens


def test_policy_engine_blocks_restricted_provider() -> None:
    engine = PolicyEngine(config={"allowed_providers": ("allowed",)})
    result = engine.evaluate(payload=_Payload(provider="blocked"), user=_User(), organization=_Org())
    assert result.allowed is False
    assert result.policy_name == "provider_restriction"


def test_governance_engine_approves_deterministically() -> None:
    engine = GovernanceEngine()

    report = asyncio.run(
        engine.govern(
            payload=_Payload(provider="allowed"),
            user=_User(),
            organization=_Org(),
            affected_runtime="AgentCorp V2",
        )
    )

    assert report.decision.allowed is True
    assert report.approval_result.state == ApprovalState.AUTO
    assert report.trace[0]["stage_name"] == "Governance Started"
    assert report.trace[-1]["stage_name"] == "Governance Completed"


def test_governance_engine_blocks_high_risk_manual_approval() -> None:
    engine = GovernanceEngine()

    report = asyncio.run(
        engine.govern(
            payload=_Payload(temperature=1.8),
            user=_User(),
            organization=_Org(),
            affected_runtime="AgentCorp V2",
        )
    )

    assert report.decision.allowed is False
    assert report.approval_result.approved is False
    assert report.execution_guard_result.allowed is False


def test_runtime_observatory_includes_runtime_governance() -> None:
    service = ObservabilityService.__new__(ObservabilityService)
    snapshot = {
        "last_runtime_governance": {"decision": True},
        "active_runtime_governance": [{"decision": True}],
    }

    async def fake_get_diagnostics():
        return snapshot

    async def fake_get_traces():
        return []

    service.get_diagnostics = fake_get_diagnostics  # type: ignore[method-assign]
    service.get_active_traces = fake_get_traces  # type: ignore[method-assign]

    observatory = asyncio.run(service.get_runtime_observatory())
    assert observatory["runtime_governance"]["decision"] is True
    assert observatory["runtime_governances"][0]["decision"] is True
