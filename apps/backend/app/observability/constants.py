"""
Observability constants.
"""

# Default slow operation thresholds in seconds
SLOW_REQUEST_THRESHOLD = 2.0
SLOW_DATABASE_THRESHOLD = 0.5
SLOW_PROVIDER_THRESHOLD = 3.0
SLOW_WORKFLOW_THRESHOLD = 5.0
SLOW_TOOL_THRESHOLD = 2.0
SLOW_RAG_THRESHOLD = 1.5
SLOW_MEMORY_THRESHOLD = 1.0

# Logging Sinks
SINK_STDOUT = "stdout"
SINK_FILE = "file"

# Audit Log actions
AUDIT_AUTH_SUCCESS = "auth.login_success"
AUDIT_AUTH_FAILURE = "auth.login_failure"
AUDIT_PERMISSION_DENIED = "auth.permission_denied"
AUDIT_TOKEN_INVALID = "auth.token_invalid"
AUDIT_PRIVILEGE_CHANGE = "auth.privilege_change"

AUDIT_ORG_CREATE = "organization.create"
AUDIT_ORG_UPDATE = "organization.update"
AUDIT_ORG_DELETE = "organization.delete"

AUDIT_TEAM_CREATE = "team.create"
AUDIT_TEAM_UPDATE = "team.update"
AUDIT_TEAM_DELETE = "team.delete"

AUDIT_AGENT_CREATE = "agent.create"
AUDIT_AGENT_UPDATE = "agent.update"
AUDIT_AGENT_DELETE = "agent.delete"

AUDIT_WORKFLOW_CREATE = "workflow.create"
AUDIT_WORKFLOW_UPDATE = "workflow.update"
AUDIT_WORKFLOW_DELETE = "workflow.delete"
AUDIT_WORKFLOW_EXECUTE = "workflow.execute"

AUDIT_KNOWLEDGE_UPLOAD = "knowledge.upload"
AUDIT_MEMORY_UPDATE = "memory.update"
AUDIT_TOOL_EXECUTE = "tool.execute"
AUDIT_GOAL_EXECUTE = "goal.execute"

AUDIT_CONFIG_CHANGE = "config.change"
AUDIT_SECURITY_EVENT = "security.event"
