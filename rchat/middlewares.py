import logging
import time

from fastapi import Request, Response

logger = logging.getLogger(__name__)


async def access_log_middleware(request: Request, call_next):
    status = None
    start_time = time.monotonic()
    try:
        response: Response = await call_next(request)
        status = response.status_code
        return response
    except Exception:
        status = 500
        raise
    finally:
        time_elapsed = time.monotonic() - start_time
        logger.info(
            "%s %.3f %s %s", status, time_elapsed, request.method, request.url
        )
