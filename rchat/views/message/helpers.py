from pydantic import UUID4

from rchat.schemas.message import Message
from rchat.state import app_state
from rchat.views.message.models import MessageSender, MessageResponse, ForeignMessage


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
            forwarded_msg_sender = await app_state.get_message_sender(forwarded_msg)
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
