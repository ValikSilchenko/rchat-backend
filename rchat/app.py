import uvicorn
from fastapi import FastAPI

from rchat.state import app_state
from rchat.views.auth.views import router as auth_router

app = FastAPI()

app.include_router(auth_router)


@app.on_event("startup")
async def startup():
    await app_state.startup()


@app.on_event("shutdown")
async def shutdown():
    await app_state.shutdown()


if __name__ == "__main__":
    uvicorn.run(
        app="rchat.app:app",
        reload=True,
        port=8000,
        host="0.0.0.0",
        access_log=False
    )
