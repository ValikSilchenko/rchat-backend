import logging
from typing import Optional

from pydantic import UUID4, UUID5

from rchat.clients.socketio_client import (
    SocketioErrorStatusEnum,
    SocketioEventsEnum,
    sio,
)
from rchat.schemas.chat import Chat, ChatCreate, ChatTypeEnum
from rchat.schemas.message import Message, MessageCreate
from rchat.state import app_state
from rchat.views.chat.helpers import get_chat_name_and_avatar
from rchat.views.message.models import (
    ActionUserParticipant,
    ChatInfo,
    CreateMessageBody,
    ForeignMessage,
    MessageResponse,
    MessageSender,
    NewMessageResponse,
    NewMessageStatusEnum,
)

logger = logging.getLogger(__name__)


async def get_foreign_message(
    message_id: Optional[UUID4],
) -> Optional[ForeignMessage]:
    if not message_id:
        return

    message = await app_state.message_repo.get_by_id(id_=message_id)
    if not message:
        return

    message_sender = await get_message_sender(message)
    return ForeignMessage(
        id=message.id,
        type=message.type,
        message_text=message.message_text,
        sender=message_sender,
    )


async def get_actioned_users(
    message: Message,
) -> tuple[ActionUserParticipant, ActionUserParticipant]:
    user_initiated_action = None
    if message.user_initiated_action_id:
        user = await app_state.user_repo.get_by_id(
            id_=message.user_initiated_action_id
        )
        user_initiated_action = ActionUserParticipant(
            id=user.id, first_name=user.first_name
        )

    user_involved = None
    if message.user_involved_id:
        user = await app_state.user_repo.get_by_id(
            id_=message.user_involved_id
        )
        user_involved = ActionUserParticipant(
            id=user.id, first_name=user.first_name
        )

    return user_initiated_action, user_involved


async def get_chat_messages_list(
    chat_id: UUID4, limit: int, last_order_id: int
):
    """
    Вспомогательный метод для получения списка сообщений.
    """
    messages = await app_state.message_repo.get_chat_messages(
        chat_id=chat_id, last_order_id=last_order_id, limit=limit
    )
    response_messages = []
    for message in messages:
        forwarded_message = await get_foreign_message(
            message.forwarded_message_id
        )
        reply_to_message = await get_foreign_message(
            message.reply_to_message_id
        )

        message_sender = await get_message_sender(message)
        read_by_users = await app_state.message_repo.get_read_user_id_list(
            message_id=message.id
        )

        user_initiated_action, user_involved = await get_actioned_users(
            message
        )

        response_messages.append(
            MessageResponse(
                **message.model_dump(),
                forwarded_message=forwarded_message,
                reply_to_message=reply_to_message,
                sender=message_sender,
                created_at=message.created_timestamp,
                read_by_users=read_by_users,
                user_initiated_action=user_initiated_action,
                user_involved=user_involved,
            )
        )
    return response_messages


async def get_message_sender(message: Message) -> MessageSender:
    """
    Возвращает модель отправителя сообщения для возврата через api.
    """
    if message.sender_user_id:
        user = await app_state.user_repo.get_by_id(id_=message.sender_user_id)
        avatar_url = (
            app_state.media_repo.get_media_url(user.avatar_photo_id)
            if user.avatar_photo_id
            else None
        )
        return MessageSender(
            user_id=user.id,
            name=user.first_name,
            avatar_photo_url=avatar_url,
        )

    chat = await app_state.chat_repo.get_by_id(chat_id=message.sender_chat_id)
    avatar_url = (
        app_state.media_repo.get_media_url(chat.avatar_photo_id)
        if chat.avatar_photo_id
        else None
    )
    return MessageSender(
        chat_id=chat.id,
        name=chat.name,
        avatar_photo_url=avatar_url,
    )


async def create_and_send_message(
    message_create: MessageCreate,
    chat: Chat,
):
    """
    Создаёт сообщение из переданной модели
    и отправляет его всем участникам чата.
    """
    message = await app_state.message_repo.create_message(
        message=message_create
    )
    chat_participants = await app_state.chat_repo.get_chat_participant_users(
        chat_id=chat.id
    )

    chat_info = ChatInfo(
        id=chat.id,
        type=chat.type,
        description=chat.description,
        created_at=chat.created_timestamp,
        is_work_chat=chat.is_work_chat,
        allow_messages_from=chat.allow_messages_from,
        allow_messages_to=chat.allow_messages_to,
    )

    user_initiated_action, user_involved = await get_actioned_users(message)

    reply_to_message = await get_foreign_message(message.reply_to_message_id)
    forwarded_message = await get_foreign_message(message.forwarded_message_id)

    message_response = NewMessageResponse(
        **message.model_dump(),
        chat=chat_info,
        sender=await get_message_sender(message),
        created_at=message.created_timestamp,
        user_initiated_action=user_initiated_action,
        user_involved=user_involved,
        reply_to_message=reply_to_message,
        forwarded_message=forwarded_message,
    )
    for participant in chat_participants:
        if participant in sio.users:
            logger.info("Message sent to user. user_id=%s", participant)
            chat_data = await get_chat_name_and_avatar(
                chat=chat, user_id=participant
            )
            message_response.chat.name = chat_data[0]
            message_response.chat.avatar_photo_url = chat_data[1]
            await sio.emit(
                event=SocketioEventsEnum.new_message,
                data=message_response.model_dump_json(),
                to=sio.users[participant],
            )


async def get_private_chat_for_new_message(
    user_id_1: UUID5, user_id_2: UUID5
) -> Chat:
    """
    Получает чат типа private для двух переданных пользователей.
    Если такого чата нету, то он создаётся,
    а пользователи добавляются как участники
    """
    chat = await app_state.chat_repo.get_private_chat_with_users(
        users_id_list=[user_id_1, user_id_2]
    )
    if not chat:
        chat = await app_state.chat_repo.create_chat(
            create_model=ChatCreate(type=ChatTypeEnum.private)
        )
        await app_state.chat_repo.add_chat_participant(
            chat_id=chat.id, user_id=user_id_1
        )
        await app_state.chat_repo.add_chat_participant(
            chat_id=chat.id, user_id=user_id_2
        )

    return chat


async def get_user_id_from_socket_session(sid: str) -> UUID5:
    """
    Получает uuid пользователя по socketio session id.
    """
    async with sio.session(sid) as io_session:
        user_id = io_session["user_id"]

    return user_id


async def mark_unread_messages_before_as_read(
    chat_id: UUID4, before_message_id: UUID4, user_id: UUID5
):
    """
    Помечает все непрочитанные сообщения до указанного как прочитанные.
    Сообщения, отправленные самим пользователем исключаются.
    """
    unread_messages_before = (
        await app_state.message_repo.get_unread_messages_before_for_user(
            chat_id=chat_id,
            before_message_id=before_message_id,
            user_id=user_id,
        )
    )
    for message_id in unread_messages_before:
        await app_state.message_repo.mark_message_as_read(
            message_id=message_id,
            read_by_user=user_id,
        )


async def validate_message_body_and_get_chat(
    message_body: CreateMessageBody, sender_user_id: UUID5, sid
) -> Optional[Chat]:
    """
    Проверяет правильность тела запроса на создание сообщения
    и возвращает модель чата для этого сообщения.

    В случае неправильного тела запроса, пользователю
    отправляется событие ошибки invalid_data.
    """
    if message_body.chat_id and message_body.other_user_public_id:
        logger.error(
            "chat_id and other_user_public_id both"
            " not allowed in new_message."
            "sender_user_id=%s",
            sender_user_id,
        )
        await sio.emit_error_event(
            to_sid=sid,
            status=SocketioErrorStatusEnum.invalid_data,
            event_name=SocketioEventsEnum.new_message,
            error_msg=NewMessageStatusEnum.two_chat_identifiers_provided,
            data=message_body.model_dump_json(),
        )
        return

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
                error_msg=NewMessageStatusEnum.user_not_found,
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
                error_msg=NewMessageStatusEnum.chat_not_found,
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
            error_msg=NewMessageStatusEnum.no_message_sender_provided,
            data=message_body.model_dump_json(),
        )
        return

    return chat
