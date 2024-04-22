from datetime import datetime, time
from enum import StrEnum

from pydantic import UUID4, UUID5, BaseModel

from rchat.schemas.chat import ChatTypeEnum, UserChatRole, UserCreatedChat
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


class BaseChatInfo(BaseModel):
    """
    Модель базовой информации о чате.
    """

    id: UUID4
    name: str
    is_work_chat: bool = False
    allow_messages_from: time | None = None
    allow_messages_to: time | None = None
    avatar_photo_url: str | None


class ChatListItem(BaseChatInfo):
    """
    Элемент списка чатов для метода получения чатов пользователя.
    """

    type: ChatTypeEnum
    created_by: UserCreatedChat | None
    last_message: LastChatMessage | None


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
    users_not_found: list[UUID5] = []
    created_chat_info: BaseChatInfo | None = None


class ChatUser(BaseModel):
    id: UUID5
    name: str
    avatar_photo_url: str | None
    chat_role: UserChatRole
    last_online: datetime | None
    can_exclude: bool


class GetChatUsersResponse(BaseModel):
    users: list[ChatUser]


class ChatUserActionStatusEnum(StrEnum):
    user_not_found = "user_not_found"
    chat_not_found = "chat_not_found"


class AddRemoveUserFromChatBody(BaseModel):
    chat_id: UUID4
    user_id: UUID5
