import time

from fastapi import Request

from app.config.logging import get_logger

logger = get_logger(__name__)


async def request_logger(request: Request, call_next):
    start = time.perf_counter()

    response = await call_next(request)

    duration = time.perf_counter() - start

    logger.info(
        "%s %s %s %.4fs",
        request.method,
        request.url.path,
        response.status_code,
        duration,
    )

    return response