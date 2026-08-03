from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config.logging import get_logger, setup_logging
from app.config.settings import settings
from app.db.init_db import initialize_database
from app.runtime.validation import validate_runtime_configuration

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()

    logger.info("Starting AgentCorp API...")

    validation_report = validate_runtime_configuration(settings)
    if not validation_report.valid:
        issues = "; ".join(f"{issue.field}: {issue.message}" for issue in validation_report.issues)
        raise RuntimeError(f"Runtime configuration validation failed: {issues}")

    initialize_database()

    logger.info("Application startup completed.")

    yield

    logger.info("Shutting down AgentCorp API...")
