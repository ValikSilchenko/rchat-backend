from fastapi import FastAPI

from rchat.clients.socketio_client import asio_app
from rchat.views.auth.views import router as auth_router
from rchat.views.chat.views import router as chat_router
from rchat.views.message.views import router as message_router
from rchat.views.user.views import router as user_router


def include_routers_and_sio(app: FastAPI):
    app.include_router(auth_router)
    app.include_router(chat_router)
    app.include_router(message_router)
    app.include_router(user_router)

    app.mount(path="/", app=asio_app)

