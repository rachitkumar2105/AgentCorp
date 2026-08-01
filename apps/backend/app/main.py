"""
Application entry point.
"""

from fastapi import FastAPI

from app.api.router import api_router
from app.config.settings import settings
from app.core.lifespan import lifespan
from app.exceptions.handlers import register_exception_handlers
from app.middleware.cors import register_cors
from app.middleware.request_logger import request_logger

app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# Register exception handlers
register_exception_handlers(app)

# Register CORS middleware
register_cors(app)

# Register request logging middleware
app.middleware("http")(request_logger)

# Register all API routes
app.include_router(api_router)