"""
Health checks endpoint routing.
"""

from datetime import datetime, timezone
from fastapi import APIRouter

from app.observability.health import check_dependency_health

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get("/")
@router.get("")
async def health():
    """
    Basic health check endpoint.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/live")
async def liveness():
    """
    Liveness probe.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/ready")
async def readiness():
    """
    Readiness probe.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/dependencies")
async def dependencies_health():
    """
    Detailed dependencies status check.
    """
    health_data = await check_dependency_health()
    return health_data