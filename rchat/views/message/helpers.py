from rchat.schemas.models import Message
from rchat.state import app_state
from rchat.views.message.models import MessageSender


async def get_message_sender(message: Message):
    """
    Возвращает модель отправителя сообщения для возврата через api.
    """
    if message.sender_user_id:
        user = await app_state.user_repo.get_by_id(id_=message.sender_user_id)
        avatar_url = app_state.media_repo.get_media_url(user.avatar_photo_id) if user.avatar_photo_id else None
        return MessageSender(
            user_id=user.id,
            name=user.first_name,
            avatar_photo_url=avatar_url,
        )

    chat = await app_state.chat_repo.get_by_id(chat_id=message.sender_chat_id)
    avatar_url = app_state.media_repo.get_media_url(chat.avatar_photo_id) if chat.avatar_photo_id else None
    return MessageSender(
        chat_id=chat.id,
        name=chat.name,
        avatar_photo_url=avatar_url,
    )
