"""
Application entry point.
"""

from fastapi import FastAPI

from app.api.router import api_router
from app.config.settings import settings
from app.core.lifespan import lifespan
from app.exceptions.handlers import register_exception_handlers
from app.middleware.cors import register_cors
from app.observability.middleware import ObservabilityMiddleware
from app.middleware.security_middleware import SecurityMiddleware
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

# Register observability middleware
app.add_middleware(ObservabilityMiddleware)
app.add_middleware(SecurityMiddleware)

# Register all API routes
app.include_router(api_router)