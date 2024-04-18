import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from rchat import migration_runner
from rchat.clients.socketio_client import asio_app
from rchat.exceptions import register_exception_handlers
from rchat.helpers import create_storage_folders
from rchat.log import setup_logging
from rchat.middlewares import access_log_middleware
from rchat.state import app_state
from rchat.views import register_routers

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    migration_runner.apply_migrations()
    create_storage_folders()
    await app_state.startup()
    yield
    await app_state.shutdown()


app = FastAPI(lifespan=lifespan)

register_routers(app)
register_exception_handlers(app)
app.mount(path="/", app=asio_app)
app.middleware("http")(access_log_middleware)


if __name__ == "__main__":
    uvicorn.run(
        app="rchat.app:app",
        reload=True,
        port=8080,
        host="0.0.0.0",
        access_log=False,
    )
