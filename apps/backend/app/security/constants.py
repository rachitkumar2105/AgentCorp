"""app/security/constants.py

Shared constants for the security package.
"""

# Rate limiting defaults (requests per minute)
DEFAULT_RATE_LIMIT = 60

# Quota defaults (e.g., AI tokens per month)
DEFAULT_AI_TOKENS_QUOTA = 1_000_000

# Permission prefixes
PERMISSION_PREFIX = "security:"

# Policy actions
ALLOW = "allow"
DENY = "deny"
CONDITIONAL = "conditional"

# Environment variable keys for secret manager
ENV_SECRET_PREFIX = "AGENTCORP_SECRET_"
