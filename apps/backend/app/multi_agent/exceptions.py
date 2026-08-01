"""
Multi-Agent Collaboration System — Domain Exceptions.
"""

from __future__ import annotations


class MultiAgentError(Exception):
    """Base exception for all multi-agent errors."""


class SessionNotFoundError(MultiAgentError):
    """Raised when a collaboration session does not exist."""


class SessionAlreadyActiveError(MultiAgentError):
    """Raised when a new session conflicts with an active one."""


class AgentNotParticipantError(MultiAgentError):
    """Raised when an agent attempts an action outside its session."""


class DelegationLimitExceededError(MultiAgentError):
    """Raised when delegation depth exceeds the allowed maximum."""


class DelegationNotFoundError(MultiAgentError):
    """Raised when a delegation record cannot be located."""


class MessageDeliveryError(MultiAgentError):
    """Raised when an inter-agent message cannot be delivered."""


class CoordinatorError(MultiAgentError):
    """Raised for coordinator-level orchestration failures."""


class ContextSyncError(MultiAgentError):
    """Raised when shared context cannot be synchronised."""
