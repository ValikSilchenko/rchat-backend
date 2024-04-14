import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError, UUID4
from starlette import status

from rchat.clients.socketio_client import sio, SocketioEventsEnum
from rchat.schemas.models import ChatTypeEnum, MessageTypeEnum, Session
from rchat.repository.message import MessageCreate
from rchat.state import app_state
from rchat.views.auth.helpers import check_access_token
from rchat.views.message.helpers import get_message_sender
from rchat.views.message.models import CreateMessageBody, MessageResponse, MessageSender, ChatMessagesResponse, \
    ForeignMessage

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Message"])


@router.get(path="/message/list", response_model=ChatMessagesResponse)
async def get_chat_messages(
        chat_id: UUID4,
        limit: int,
        last_order_id: int = 0,
        session: Session = Depends(check_access_token),
):
    chat_participants = await app_state.chat_repo.get_chat_participant_users(chat_id)
    if session.user_id not in chat_participants:
        logger.error(
            "User not in chat. chat_id=%s, user_id=%s, session=%s",
            chat_id,
            session.user_id,
            session.id,
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_not_in_chat")

    messages = await app_state.message_repo.get_chat_messages(
        chat_id=chat_id, last_order_id=last_order_id, limit=limit
    )
    response_messages = []
    for message in messages:
        forwarded_msg = await app_state.message_repo.get_by_id(id_=message.forwarded_message)
        if forwarded_msg:
            forwarded_msg_sender = await get_message_sender(forwarded_msg)
            forwarded_message = ForeignMessage(
                id=forwarded_msg.id,
                type=forwarded_msg.type,
                message_text=forwarded_msg.message_text,
                sender=forwarded_msg_sender,
            )
        else:
            forwarded_message = None

        replied_msg = await app_state.message_repo.get_by_id(id_=message.reply_to_message)
        if replied_msg:
            replied_msg_sender = await get_message_sender(replied_msg)
            reply_to_message = ForeignMessage(
                id=replied_msg.id,
                type=replied_msg.type,
                message_text=replied_msg.message_text,
                sender=replied_msg_sender,
            )
        else:
            reply_to_message = None

        message_sender = await get_message_sender(message)
        response_messages.append(
            MessageResponse(
                **message.model_dump(exclude={"forwarded_message", "reply_to_message"}),
                forwarded_message=forwarded_message,
                reply_to_message=reply_to_message,
                sender=message_sender,
                created_at=message.created_timestamp,
            )
        )

    return ChatMessagesResponse(messages=response_messages)


@sio.on("_new_message_")
async def handle_new_message(sid, data: dict, *args):
    try:
        message_body = CreateMessageBody(**data)
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
    chat_participants = await app_state.chat_repo.get_chat_participant_users(chat_id=chat.id)

    sender = MessageSender(
        user_id=sender_user.id,
        name=sender_user.public_id
    )
    message_response = MessageResponse(
        **message.model_dump(), sender=sender, created_at=message.created_timestamp
    )
    for participant in chat_participants:
        logger.info("user_id: %s", participant)
        if participant in sio.users:
            logger.info("sio: %s", sio.users.get(participant))
            await sio.emit(
                event=SocketioEventsEnum.new_message,
                data=message_response.model_dump_json(),
                to=sio.users[participant],
            )
