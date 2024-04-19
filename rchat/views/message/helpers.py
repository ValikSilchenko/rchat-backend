import logging

from pydantic import UUID4, UUID5

from rchat.clients.socketio_client import SocketioEventsEnum, sio
from rchat.schemas.chat import Chat, ChatTypeEnum, ChatCreate
from rchat.schemas.message import Message, MessageCreate
from rchat.state import app_state
from rchat.views.chat.helpers import get_chat_name
from rchat.views.message.models import (
    ChatInfo,
    ForeignMessage,
    MessageResponse,
    MessageSender,
    NewMessageResponse,
)

logger = logging.getLogger(__name__)


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
        forwarded_msg = await app_state.message_repo.get_by_id(
            id_=message.forwarded_message
        )
        if forwarded_msg:
            forwarded_msg_sender = await app_state.get_message_sender(
                forwarded_msg
            )
            forwarded_message = ForeignMessage(
                id=forwarded_msg.id,
                type=forwarded_msg.type,
                message_text=forwarded_msg.message_text,
                sender=forwarded_msg_sender,
            )
        else:
            forwarded_message = None

        replied_msg = await app_state.message_repo.get_by_id(
            id_=message.reply_to_message
        )
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
                **message.model_dump(
                    exclude={"forwarded_message", "reply_to_message"}
                ),
                forwarded_message=forwarded_message,
                reply_to_message=reply_to_message,
                sender=message_sender,
                created_at=message.created_timestamp,
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


async def create_and_send_message(message_create: MessageCreate, chat: Chat):
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
