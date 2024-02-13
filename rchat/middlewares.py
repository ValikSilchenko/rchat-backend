import logging

from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


async def access_log_middleware(request: Request, call_next):
    status = None
    try:
        response: Response = await call_next(request)
        status = response.status_code
        return response
    except Exception:
        status = 500
        raise
    finally:
        logger.info("%s %s %s", status, request.method, request.url)
