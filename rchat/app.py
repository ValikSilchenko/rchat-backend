import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

import rchat.clients.socketio_client as sio_client
from rchat import migration_runner
from rchat.exceptions import register_exception_handlers
from rchat.helpers import create_storage_folders
from rchat.log import setup_logging
from rchat.middlewares import access_log_middleware
from rchat.state import app_state
from rchat.views.auth.views import router as auth_router
from rchat.views.chat.views import router as chat_router
from rchat.views.message.views import router as message_router
from rchat.views.user.views import router as user_router

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

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(message_router)
app.include_router(user_router)
app.mount(path="/", app=sio_client.asio_app)
register_exception_handlers(app)
app.middleware("http")(access_log_middleware)


if __name__ == "__main__":
    uvicorn.run(
        app="rchat.app:app",
        reload=True,
        port=8080,
        host="0.0.0.0",
        access_log=False,
    )
