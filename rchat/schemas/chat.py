import uuid
from datetime import datetime, time
from enum import StrEnum

from pydantic import UUID4, UUID5, BaseModel


class ChatTypeEnum(StrEnum):
    private = "private"
    group = "group"
    channel = "channel"


class ChatCreate(BaseModel):
    id: UUID4 = uuid.uuid4()
    type: ChatTypeEnum
    name: str | None
    created_by: UUID5 | None
    avatar_photo_id: UUID4 | None
    description: str | None
    is_work_chat: bool
    allow_messages_from: time | None
    allow_messages_to: time | None


class Chat(BaseModel):
    id: UUID4
    type: ChatTypeEnum
    name: str | None
    created_by: UUID5 | None
    avatar_photo_id: UUID4 | None
    description: str | None
    is_work_chat: bool
    allow_messages_from: time | None
    allow_messages_to: time | None
    created_timestamp: datetime


class ChatParticipant(BaseModel):
    chat_id: UUID4
    user_id: UUID5
    added_by_user: UUID5
    is_chat_owner: bool
    last_available_message: UUID4 | None
    created_timestamp: datetime
