import logging
import uuid
from datetime import datetime

from fastapi import APIRouter

from rchat.clients.socketio_client import sio

logger = logging.getLogger(__name__)

router = APIRouter()


@sio.on("_new_message_")
async def handle_new_message(sid, data: dict):
    logger.info("Got message. params=%s", {"sid": sid, "data": data})

    data["id"] = uuid.uuid4().hex
    data["created_at"] = str(datetime.now())
    await sio.emit(event="_new_message_", data=data)
