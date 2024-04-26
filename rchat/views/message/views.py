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
    get_user_id_from_socket_session,
)
from rchat.views.message.models import (
    ChatMessagesResponse,
    ChatMessagesStatusEnum,
    CreateMessageBody,
    NewMessageEventStatusEnum,
    ReadMessageBody,
    ReadMessageResponse,
    ReadMessageStatusEnum,
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
    sender_user_id = await get_user_id_from_socket_session(sid)

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
        message_create=message_create_model,
        chat=chat,
    )


@sio.on(SocketioEventsEnum.read_message)
async def handle_read_message(sid, read_message_body: ReadMessageBody):
    user_id = await get_user_id_from_socket_session(sid)

    message = await app_state.message_repo.get_by_id(
        id_=read_message_body.message_id
    )
    if not message or message.chat_id != read_message_body.chat_id:
        logger.error(
            "Message not found. message_id=%s, user_id=%s",
            read_message_body.message_id,
            user_id,
        )
        await sio.emit_error_event(
            to_sid=sid,
            status=SocketioErrorStatusEnum.invalid_data,
            event_name=SocketioEventsEnum.read_message,
            error_msg=ReadMessageStatusEnum.message_not_found,
            data=read_message_body.model_dump_json(),
        )
        return

    chat_participants = await app_state.chat_repo.get_chat_participant_users(
        chat_id=message.chat_id
    )
    if user_id not in chat_participants:
        logger.error(
            "User not in chat. chat_id=%s, user_id=%s",
            message.chat_id,
            user_id,
        )
        await sio.emit_error_event(
            to_sid=sid,
            status=SocketioErrorStatusEnum.invalid_data,
            event_name=SocketioEventsEnum.read_message,
            error_msg=ReadMessageStatusEnum.user_not_in_chat,
            data=read_message_body.model_dump_json(),
        )
        return

    if user_id == message.sender_user_id:
        logger.error(
            "Cannot read own message. message_id=%s, user_id=%s",
            message.id,
            user_id,
        )
        await sio.emit_error_event(
            to_sid=sid,
            status=SocketioErrorStatusEnum.invalid_data,
            event_name=SocketioEventsEnum.read_message,
            error_msg=ReadMessageStatusEnum.user_cannot_read_own_message,
            data=read_message_body.model_dump_json(),
        )
        return

    is_marked = await app_state.message_repo.mark_message_as_read(
        message_id=read_message_body.message_id,
        read_by_user=user_id,
    )
    if not is_marked:
        logger.error(
            "User already read the message. message_id=%s, user_id=%s",
            message.id,
            user_id,
        )
        await sio.emit_error_event(
            to_sid=sid,
            status=SocketioErrorStatusEnum.invalid_data,
            event_name=SocketioEventsEnum.read_message,
            error_msg=ReadMessageStatusEnum.user_already_read_the_message,
            data=read_message_body.model_dump_json(),
        )
        return

    read_message_response = ReadMessageResponse(
        chat_id=message.chat_id, message_id=message.id, read_by_user=user_id
    )
    for user in chat_participants:
        if user in sio.users:
            await sio.emit(
                event=SocketioEventsEnum.read_message,
                to=sio.users[user],
                data=read_message_response.model_dump_json(),
            )
