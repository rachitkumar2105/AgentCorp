"""
Main API router.

Registers all endpoint routers in a single place so that main.py stays
clean.  Add new routers here — never in main.py directly.
"""

from fastapi import APIRouter

from app.api.endpoints import (
    admin,
    auth,
    health,
    organization_members,
    organizations,
    permissions,
    role_permissions,
    roles,
    root,
    team_members,
    teams,
    tools,
    agent_tools,
    user_roles,
    users,
)
from app.api.v1 import chat as chat_v1
from app.api.v1 import streaming as streaming_v1
from app.api.v1 import knowledge as knowledge_v1
from app.api.v1 import rag as rag_v1
from app.api.v1 import memory as memory_v1
from app.api.v1 import workflow as workflow_v1
from app.api.v1 import agent_engine as agent_engine_v1
from app.api.v1 import multi_agent as multi_agent_v1
from app.api.v1 import observability as observability_v1
from app.api.v1 import security as security_v1




api_router = APIRouter()

api_router.include_router(root.router)
api_router.include_router(health.router)

# Observability APIs (Metrics, Audit logs, Diagnostics)
api_router.include_router(observability_v1.router, prefix="/api/v1")

# Authentication
api_router.include_router(auth.router)

# Users
api_router.include_router(users.router)

# RBAC
api_router.include_router(roles.router)
api_router.include_router(permissions.router)
api_router.include_router(role_permissions.router)
api_router.include_router(user_roles.router)

# Organizations
api_router.include_router(organizations.router)
api_router.include_router(organization_members.router)

# Teams
api_router.include_router(teams.router)
api_router.include_router(team_members.router)

# Tools & Agent Tools
api_router.include_router(tools.router)
api_router.include_router(agent_tools.router)

# Chat Engine (v1) — must come before streaming so /stream suffix routes resolve correctly
api_router.include_router(chat_v1.router)

# Streaming Engine (v1)
api_router.include_router(streaming_v1.router)
api_router.include_router(streaming_v1.metrics_router)

# Knowledge Base Management System
api_router.include_router(knowledge_v1.router)
api_router.include_router(knowledge_v1.doc_router)

# RAG Engine
api_router.include_router(rag_v1.router)

# Memory Engine
api_router.include_router(memory_v1.router)
api_router.include_router(memory_v1.summary_router)

# Workflow Engine
api_router.include_router(workflow_v1.router)

# Agent Engine
api_router.include_router(agent_engine_v1.router)

# Multi-Agent Collaboration
api_router.include_router(multi_agent_v1.router)

# Security, Governance & Compliance
api_router.include_router(security_v1.router)




# Admin
api_router.include_router(admin.router)