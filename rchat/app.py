import uvicorn
from fastapi import FastAPI

from rchat.middlewares import access_log_middleware
from rchat.state import app_state
from rchat.views.auth.views import router as auth_router

import logging

app = FastAPI()

app.include_router(auth_router)

logging.basicConfig(level=logging.INFO)


@app.on_event("startup")
async def startup():
    await app_state.startup()
    await app_state.init_migrations()


@app.on_event("shutdown")
async def shutdown():
    await app_state.shutdown()


app.middleware("http")(access_log_middleware)


if __name__ == "__main__":
    uvicorn.run(
        app="rchat.app:app",
        reload=True,
        port=8080,
        host="0.0.0.0",
        access_log=False,
    )
