from fastapi import FastAPI

from rchat.views.auth.views import router as auth_router
from rchat.views.chat.views import router as chat_router
from rchat.views.message.views import router as message_router
from rchat.views.user.views import router as user_router


def register_routers(app: FastAPI):
    """
    Регистрирует роутеры api.
    """
    app.include_router(auth_router)
    app.include_router(chat_router)
    app.include_router(message_router)
    app.include_router(user_router)
