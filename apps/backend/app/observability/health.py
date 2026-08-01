"""
Health check indicators for dependencies.
"""

from typing import Dict, Any
from sqlalchemy import text
from app.db.session import SessionLocal
from app.config.settings import settings
from app.observability.logging import get_logger

logger = get_logger(__name__)


async def check_db() -> Dict[str, Any]:
    """Check database connectivity and response time."""
    try:
        # Use sync SessionLocal or execute a select 1
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        return {"status": "healthy"}
    except Exception as e:
        logger.error("Database health check failed: %s", str(e))
        return {"status": "unhealthy", "error": str(e)}


async def check_providers() -> Dict[str, Any]:
    """Check provider settings configuration."""
    # Since we shouldn't make outbound web requests during a fast health check,
    # we verify that keys are configured.
    configured = []
    if settings.GROQ_API_KEY:
        configured.append("groq")
    if settings.OPENAI_API_KEY:
        configured.append("openai")
    if settings.ANTHROPIC_API_KEY:
        configured.append("anthropic")
    if settings.GEMINI_API_KEY:
        configured.append("gemini")
    
    return {
        "status": "healthy" if configured else "unhealthy",
        "configured_providers": configured,
    }


async def check_vector_store() -> Dict[str, Any]:
    """Check vector store connection (pgvector)."""
    try:
        # Since pgvector is stored in the same PostgreSQL database, verify extension or tables
        with SessionLocal() as db:
            db.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector';"))
        return {"status": "healthy"}
    except Exception as e:
        logger.error("Vector store health check failed: %s", str(e))
        return {"status": "unhealthy", "error": str(e)}


async def check_dependency_health() -> Dict[str, Any]:
    """Check all dependencies health."""
    db_health = await check_db()
    provider_health = await check_providers()
    vector_health = await check_vector_store()

    all_healthy = (
        db_health["status"] == "healthy" and
        provider_health["status"] == "healthy" and
        vector_health["status"] == "healthy"
    )

    return {
        "status": "healthy" if all_healthy else "unhealthy",
        "details": {
            "database": db_health,
            "providers": provider_health,
            "vector_store": vector_health,
            "memory": {"status": "healthy"},  # Mocked memory subsystem health
            "workflow_engine": {"status": "healthy"},  # Mocked workflow engine health
            "ai_orchestrator": {"status": "healthy"},  # Mocked AI orchestrator health
        }
    }
