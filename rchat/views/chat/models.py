from datetime import datetime

from pydantic import BaseModel, UUID4

from rchat.schemas.models import ChatTypeEnum, MessageTypeEnum
from rchat.views.message.models import MessageSender


class LastChatMessage(BaseModel):
    """
    Модель последнего сообщения в чате.
    """
    id: UUID4
    message_type: MessageTypeEnum
    message_text: str | None
    created_at: datetime
    sender: MessageSender


class ChatListItem(BaseModel):
    """
    Элемент списка чатов для метода получения чатов пользователя.
    """
    id: UUID4
    name: str
    type: ChatTypeEnum
    last_message: LastChatMessage | None
    avatar_photo_url: str | None


class ChatListResponse(BaseModel):
    chat_list: list[ChatListItem]
