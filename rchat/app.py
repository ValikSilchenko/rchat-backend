import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from rchat import migration_runner
from rchat.conf import ENVIRONMENT, RELOAD_ENABLED
from rchat.exceptions import register_exception_handlers
from rchat.helpers import create_storage_folders
from rchat.log import setup_logging
from rchat.middlewares import access_log_middleware
from rchat.state import app_state
from rchat.views import include_routers_and_sio

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    migration_runner.apply_migrations()
    create_storage_folders()
    if ENVIRONMENT == "dev":
        await asyncio.sleep(5)
    await app_state.startup()
    yield
    await app_state.shutdown()


app = FastAPI(lifespan=lifespan)

include_routers_and_sio(app)
register_exception_handlers(app)
app.middleware("http")(access_log_middleware)


if __name__ == "__main__":
    uvicorn.run(
        app="rchat.app:app",
        reload=RELOAD_ENABLED,
        port=8080,
        host="0.0.0.0",
        access_log=False,
        http="h11",
    )
