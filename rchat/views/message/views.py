import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import UUID4
from starlette import status

from rchat.clients.socketio_client import (
    SocketioErrorStatusEnum,
    SocketioEventsEnum,
    sio,
)
from rchat.repository.message import MessageCreate
from rchat.schemas.message import MessageTypeEnum
from rchat.schemas.session import Session
from rchat.state import app_state
from rchat.views.auth.helpers import check_access_token
from rchat.views.message.helpers import (
    create_and_send_message,
    get_chat_messages_list,
    get_private_chat_for_new_message,
)
from rchat.views.message.models import (
    ChatMessagesResponse,
    ChatMessagesStatusEnum,
    CreateMessageBody,
    NewMessageEventStatusEnum,
)

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
    chat = await app_state.chat_repo.get_by_id(chat_id)
    if not chat:
        logger.error(
            "Chat not found. chat_id=%s, session=%s", chat_id, session.id
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ChatMessagesStatusEnum.chat_not_found,
        )

    chat_participants = await app_state.chat_repo.get_chat_participant_users(
        chat_id
    )
    if session.user_id not in chat_participants:
        logger.error(
            "User not in chat. chat_id=%s, session=%s",
            chat_id,
            session.id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ChatMessagesStatusEnum.user_not_in_chat,
        )

    response_messages = await get_chat_messages_list(
        chat_id=chat_id, limit=limit, last_order_id=last_order_id
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
        sender_user_id = io_session["user_id"]

    if message_body.other_user_public_id:
        other_user = await app_state.user_repo.get_by_public_id(
            message_body.other_user_public_id
        )
        if not other_user:
            logger.error(
                "Other user not found."
                " other_user_public_id=%s, sender_user_id=%s",
                message_body.other_user_public_id,
                sender_user_id,
            )
            await sio.emit_error_event(
                to_sid=sid,
                status=SocketioErrorStatusEnum.invalid_data,
                event_name=SocketioEventsEnum.new_message,
                error_msg=NewMessageEventStatusEnum.user_not_found,
                data=message_body.model_dump_json(),
            )
            return

        chat = await get_private_chat_for_new_message(
            user_id_1=sender_user_id, user_id_2=other_user.id
        )
    elif message_body.chat_id:
        chat = await app_state.chat_repo.get_by_id(
            chat_id=message_body.chat_id
        )
        if not chat:
            logger.error(
                "Chat not found. chat_id=%s, sender_user_id=%s",
                message_body.chat_id,
                sender_user_id,
            )
            await sio.emit_error_event(
                to_sid=sid,
                status=SocketioErrorStatusEnum.invalid_data,
                event_name=SocketioEventsEnum.new_message,
                error_msg=NewMessageEventStatusEnum.chat_not_found,
                data=message_body.model_dump_json(),
            )
            return
    else:
        logger.error(
            "No sender were provided. sender_user_id=%s",
            sender_user_id,
        )
        await sio.emit_error_event(
            to_sid=sid,
            status=SocketioErrorStatusEnum.invalid_data,
            event_name=SocketioEventsEnum.new_message,
            error_msg=NewMessageEventStatusEnum.no_message_sender_provided,
            data=message_body.model_dump_json(),
        )
        return

    message_create_model = MessageCreate(
        **message_body.model_dump(exclude={"chat_id"}),
        id=uuid.uuid4(),
        chat_id=chat.id,
        type=MessageTypeEnum.text,
        sender_user_id=sender_user_id,
    )
    await create_and_send_message(
        message_create=message_create_model, chat=chat
    )
