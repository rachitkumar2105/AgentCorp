from fastapi import APIRouter

from app.config.settings import settings

router = APIRouter(tags=["Root"])


@router.get("/")
async def root():
    """
    Root endpoint.
    """

    return {
        "application": settings.APP_NAME,
        "description": settings.APP_DESCRIPTION,
        "version": settings.APP_VERSION,
        "status": "running",
        "message": "Welcome to AgentCorp 🚀",
    }