from datetime import datetime, time
from enum import StrEnum

from pydantic import UUID4, UUID5, BaseModel

from rchat.schemas.chat import ChatTypeEnum
from rchat.schemas.message import MessageTypeEnum
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
    is_work_chat: bool = False
    allow_messages_from: time | None
    allow_messages_to: time | None
    last_message: LastChatMessage | None
    avatar_photo_url: str | None


class ChatListResponse(BaseModel):
    chat_list: list[ChatListItem]


class CreateGroupChatBody(BaseModel):
    user_id_list: list[UUID5]
    name: str | None = None
    description: str | None = None
    is_work_chat: bool = False
    allow_messages_from: time | None = None
    allow_messages_to: time | None = None


class CreateGroupChatStatusEnum(StrEnum):
    ok = "ok"
    users_not_found = "users_not_found"


class CreateGroupChatResponse(BaseModel):
    status: CreateGroupChatStatusEnum = CreateGroupChatStatusEnum.ok
    chat_id: UUID4 | None = None
    chat_name: str | None = None
    is_work_chat: bool | None = None
    users_not_found: list[UUID5]
