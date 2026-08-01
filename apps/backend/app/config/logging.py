import logging
from app.observability.logging import setup_structured_logging, get_logger as get_structured_logger


def setup_logging() -> None:
    setup_structured_logging(sink="stdout")


def get_logger(name: str) -> logging.Logger:
    return get_structured_logger(name)