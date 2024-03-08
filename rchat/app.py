import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError

from rchat.log import setup_logging
from rchat.middlewares import access_log_middleware
from rchat.state import app_state
from rchat.views.auth.views import router as auth_router
from rchat.views.user.views import router as user_router

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await app_state.startup()
    yield
    await app_state.shutdown()


app = FastAPI(lifespan=lifespan)

app.include_router(auth_router)
app.include_router(user_router)

app.middleware("http")(access_log_middleware)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request, error):
    logger.error("Validation error=%s", error)
    return await request_validation_exception_handler(request, error)


if __name__ == "__main__":
    uvicorn.run(
        app="rchat.app:app",
        reload=True,
        port=8080,
        host="0.0.0.0",
        access_log=False,
    )
