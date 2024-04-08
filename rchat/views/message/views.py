import logging
import uuid

from fastapi import APIRouter
from pydantic import ValidationError

from rchat.clients.socketio_client import sio, SocketioEventsEnum
from rchat.schemas.models import ChatTypeEnum, MessageTypeEnum
from rchat.repository.message import MessageCreate
from rchat.state import app_state
from rchat.views.message.models import NewMessageBody, NewMessageResponse, MessageSender

logger = logging.getLogger(__name__)

router = APIRouter()


@sio.on("_new_message_")
async def handle_new_message(sid, data: dict, *args):
    try:
        message_body = NewMessageBody(**data)
    except ValidationError:
        return

    async with sio.session(sid) as io_session:
        sender_user = await app_state.user_repo.get_by_id(id_=io_session["user_id"])

    if message_body.user_public_id:
        user = await app_state.user_repo.get_by_public_id(message_body.user_public_id)
        chat = await app_state.chat_repo.create_chat(chat_type=ChatTypeEnum.private)

        await app_state.chat_repo.add_chat_participant(chat_id=chat.id, user_id=sender_user.id)
        await app_state.chat_repo.add_chat_participant(chat_id=chat.id, user_id=user.id)
    elif message_body.chat_id:
        chat = await app_state.chat_repo.get_by_id(chat_id=message_body.chat_id)
    else:
        return  # TODO Добавить обработку ошибки

    msg_type = MessageTypeEnum.text
    message = await app_state.message_repo.create_message(
        message=MessageCreate(
            **message_body.model_dump(exclude={"chat_id"}),
            id=uuid.uuid4(),
            chat_id=chat.id,
            type=msg_type,
        )
    )
    chat_participants = await app_state.chat_repo.get_chat_participants(chat_id=chat.id)

    sender = MessageSender(
        user_id=sender_user.id,
        name=sender_user.public_id
    )
    message_response = NewMessageResponse(
        **message.model_dump(), sender=sender, created_at=message.created_timestamp
    )
    for participant in chat_participants:
        logger.info("user_id: %s", participant.user_id)
        if participant.user_id in sio.users:
            logger.info("sio: %s", sio.users.get(participant.user_id))
            await sio.emit(
                event=SocketioEventsEnum.new_message,
                data=message_response.model_dump_json(),
                to=sio.users[participant.user_id],
            )
