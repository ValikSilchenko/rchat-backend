import logging

from fastapi import FastAPI
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError

logger = logging.getLogger(__name__)


async def validation_error_handler(request, error):
    logger.error("Validation error=%s", error)
    return await request_validation_exception_handler(request, error)


def register_exception_handlers(app: FastAPI):
    """
    Регистрирует обработчики ошибок.
    """
    app.add_exception_handler(
        exc_class_or_status_code=RequestValidationError,
        handler=validation_error_handler,
    )
