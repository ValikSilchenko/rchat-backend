from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from rchat.log import setup_logging
from rchat.middlewares import access_log_middleware
from rchat.state import app_state
from rchat.views.auth.views import router as auth_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await app_state.startup()
    setup_logging()
    yield
    await app_state.shutdown()


app = FastAPI(lifespan=lifespan)

app.include_router(auth_router)

app.middleware("http")(access_log_middleware)


if __name__ == "__main__":
    uvicorn.run(
        app="rchat.app:app",
        reload=True,
        port=8080,
        host="0.0.0.0",
        access_log=False,
    )
