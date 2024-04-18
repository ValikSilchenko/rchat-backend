from datetime import datetime
from enum import StrEnum

from pydantic import UUID4, UUID5, BaseModel


class ChatTypeEnum(StrEnum):
    private = "private"
    group = "group"
    channel = "channel"


class Chat(BaseModel):
    id: UUID4
    type: ChatTypeEnum
    name: str | None
    avatar_photo_id: UUID4 | None
    description: str | None
    created_timestamp: datetime


class ChatParticipant(BaseModel):
    chat_id: UUID4
    user_id: UUID5
    is_chat_owner: bool
    last_available_message: UUID4 | None
    created_timestamp: datetime
