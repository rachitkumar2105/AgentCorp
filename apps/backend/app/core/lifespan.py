from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config.logging import get_logger, setup_logging
from app.db.init_db import initialize_database

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()

    logger.info("Starting AgentCorp API...")

    initialize_database()

    logger.info("Application startup completed.")

    yield

    logger.info("Shutting down AgentCorp API...")