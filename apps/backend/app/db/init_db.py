"""
Database initialization utilities.

This module is responsible for validating the database connection during
application startup and provides a single place for future database
initialization tasks such as:

- Connection verification
- Running startup checks
- Database seeding
- Cache warming
- Migration validation
"""

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.config.logging import get_logger
from app.db.session import engine

logger = get_logger(__name__)


def check_database_connection() -> bool:
    """
    Verify that the application can connect to the database.

    Returns:
        bool: True if the database is reachable, otherwise False.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        logger.info("Database connection established successfully.")
        return True

    except SQLAlchemyError as exc:
        logger.exception("Database connection failed: %s", exc)
        return False


def initialize_database() -> None:
    """
    Perform all database initialization tasks.

    This function should be called once during application startup.

    Future responsibilities:
        - Validate migrations
        - Seed default data
        - Initialize extensions
        - Perform startup health checks
    """
    logger.info("Initializing database...")

    if not check_database_connection():
        raise RuntimeError("Unable to establish database connection.")

    logger.info("Database initialization completed successfully.")