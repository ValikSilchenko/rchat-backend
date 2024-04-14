import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError, UUID4
from starlette import status

from rchat.clients.socketio_client import sio, SocketioEventsEnum, SocketioErrorStatusEnum
from rchat.schemas.models import ChatTypeEnum, MessageTypeEnum, Session
from rchat.repository.message import MessageCreate
from rchat.state import app_state
from rchat.views.auth.helpers import check_access_token
from rchat.views.message.helpers import get_message_sender
from rchat.views.message.models import CreateMessageBody, MessageResponse, MessageSender, ChatMessagesResponse, \
    ForeignMessage, NewMessageEventStatusEnum

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Message"])


@router.get(path="/message/list", response_model=ChatMessagesResponse)
async def get_chat_messages(
        chat_id: UUID4,
        limit: int,
        last_order_id: int = 0,
        session: Session = Depends(check_access_token),
):
    """
    Получает список сообщений
    с информацией о пересланных и отвеченных сообщениях,
    а также отправителях этих сообщений и главного сообщения.

    Сообщения отсортированы в порядке убывания даты.
    """
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


@sio.on(SocketioEventsEnum.new_message)
async def handle_new_message(sid, message_body: CreateMessageBody):
    """
    Метод обработки нового сообщения от пользователей.

    Если сообщение написано пользователю, с которым у отправителя нету чата,
    То создаётся чат и оба пользователя добавляются как участники чата.
    """
    async with sio.session(sid) as io_session:
        sender_user = await app_state.user_repo.get_by_id(id_=io_session["user_id"])

    if message_body.other_user_public_id:
        other_user = await app_state.user_repo.get_by_public_id(message_body.other_user_public_id)
        if not other_user:
            logger.error(
                "Other user not found."
                " other_user_public_id=%s, sender_user_id=%s",
                message_body.other_user_public_id,
                sender_user.id,
            )
            await sio.emit_error_event(
                to_sid=sid,
                status=SocketioErrorStatusEnum.invalid_data,
                event_name=SocketioEventsEnum.new_message,
                error_msg=NewMessageEventStatusEnum.user_not_found,
                data=message_body.model_dump()
            )
            return

        chat = await app_state.chat_repo.get_private_chat_with_users(
            users_id_list=[sender_user.id, other_user.id]
        )
        if not chat:
            chat = await app_state.chat_repo.create_chat(chat_type=ChatTypeEnum.private)
            await app_state.chat_repo.add_chat_participant(chat_id=chat.id, user_id=sender_user.id)
            await app_state.chat_repo.add_chat_participant(chat_id=chat.id, user_id=other_user.id)
    elif message_body.chat_id:
        chat = await app_state.chat_repo.get_by_id(chat_id=message_body.chat_id)
        if not chat:
            logger.error(
                "Chat not found. chat_id=%s, sender_user_id=%s",
                message_body.chat_id,
                sender_user.id,
            )
            await sio.emit_error_event(
                to_sid=sid,
                status=SocketioErrorStatusEnum.invalid_data,
                event_name=SocketioEventsEnum.new_message,
                error_msg=NewMessageEventStatusEnum.chat_not_found,
                data=message_body.model_dump()
            )
            return
    else:
        logger.error(
            "No sender were provided. sender_user_id=%s",
            sender_user.id,
        )
        await sio.emit_error_event(
            to_sid=sid,
            status=SocketioErrorStatusEnum.invalid_data,
            event_name=SocketioEventsEnum.new_message,
            error_msg=NewMessageEventStatusEnum.no_message_sender_provided,
            data=message_body.model_dump()
        )
        return

    message = await app_state.message_repo.create_message(
        message=MessageCreate(
            **message_body.model_dump(exclude={"chat_id"}),
            id=uuid.uuid4(),
            chat_id=chat.id,
            type=MessageTypeEnum.text,
            sender_user_id=sender_user.id,
        )
    )
    chat_participants = await app_state.chat_repo.get_chat_participant_users(chat_id=chat.id)

    message_response = MessageResponse(
        **message.model_dump(),
        sender=await get_message_sender(message),
        created_at=message.created_timestamp,
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
