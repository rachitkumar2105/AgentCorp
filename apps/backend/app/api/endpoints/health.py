from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get("/")
async def health():
    """
    Health check endpoint.
    """

    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }