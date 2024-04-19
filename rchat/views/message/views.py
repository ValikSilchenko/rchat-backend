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
from rchat.schemas.chat import ChatTypeEnum
from rchat.schemas.message import MessageTypeEnum
from rchat.schemas.session import Session
from rchat.state import app_state
from rchat.views.auth.helpers import check_access_token
from rchat.views.chat.helpers import get_chat_name
from rchat.views.message.helpers import get_message_sender
from rchat.views.message.models import (
    ChatInfo,
    ChatMessagesResponse,
    ChatMessagesStatusEnum,
    CreateMessageBody,
    ForeignMessage,
    MessageResponse,
    NewMessageEventStatusEnum,
    NewMessageResponse,
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
    is_chat_exists = await app_state.message_service.is_chat_exist(chat_id=chat_id)
    if not is_chat_exists:
        logger.error(
            "Chat not found. chat_id=%s, session=%s", chat_id, session.id
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ChatMessagesStatusEnum.chat_not_found,
        )

    is_chat_participant = (
        await app_state.message_service.is_user_chat_participant(
            user_id=session.user_id, chat_id=chat_id
        )
    )
    if not is_chat_participant:
        logger.error(
            "User not in chat. chat_id=%s, session=%s",
            chat_id,
            session.id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ChatMessagesStatusEnum.user_not_in_chat,
        )

    response_messages = (
        await app_state.message_service.get_chat_messages_list(
            chat_id=chat_id,
            limi=limit,
            last_order_id=last_order_id,
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
        sender_user = await app_state.user_repo.get_by_id(
            id_=io_session["user_id"]
        )

    if message_body.other_user_public_id:
        other_user = await app_state.user_repo.get_by_public_id(
            message_body.other_user_public_id
        )
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
                data=message_body.model_dump(),
            )
            return

        chat = await app_state.chat_repo.get_private_chat_with_users(
            users_id_list=[sender_user.id, other_user.id]
        )
        if not chat:
            chat = await app_state.chat_repo.create_chat(
                chat_type=ChatTypeEnum.private
            )
            await app_state.chat_repo.add_chat_participant(
                chat_id=chat.id, user_id=sender_user.id
            )
            await app_state.chat_repo.add_chat_participant(
                chat_id=chat.id, user_id=other_user.id
            )
    elif message_body.chat_id:
        chat = await app_state.chat_repo.get_by_id(
            chat_id=message_body.chat_id
        )
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
                data=message_body.model_dump(),
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
            data=message_body.model_dump(),
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
    chat_participants = await app_state.chat_repo.get_chat_participant_users(
        chat_id=chat.id
    )
    chat_avatar = (
        app_state.media_repo.get_media_url(id_=chat.avatar_photo_id)
        if chat.avatar_photo_id
        else None
    )

    message_response = NewMessageResponse(
        **message.model_dump(),
        chat=ChatInfo(
            id=chat.id,
            type=chat.type,
            avatar_photo_url=chat_avatar,
            description=chat.description,
            created_at=chat.created_timestamp,
        ),
        sender=await get_message_sender(message),
        created_at=message.created_timestamp,
    )
    for participant in chat_participants:
        if participant in sio.users:
            logger.info("Message sent to user. user_id=%s", participant)
            message_response.chat.name = await get_chat_name(
                chat=chat, user_id=participant
            )
            await sio.emit(
                event=SocketioEventsEnum.new_message,
                data=message_response.model_dump_json(),
                to=sio.users[participant],
            )
