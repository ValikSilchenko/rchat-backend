import logging

import socketio

logger = logging.getLogger(__name__)


sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins=["*"])

asio_app = socketio.ASGIApp(socketio_server=sio, socketio_path="socks")


@sio.event
async def connect(sid, environ, auth):
    logger.info("Socketio connected. params=%s", {"sid": sid, "auth": auth})


@sio.event
async def message(sid, environ):
    logger.info("Got message. params=%s", {"sid": sid, "environ": environ})
    await sio.emit(event="message", data={"message": "Hello"})


@sio.event
async def disconnect(sid):
    logger.info("Socketio disconnected. params=%s", {"sid": sid})
