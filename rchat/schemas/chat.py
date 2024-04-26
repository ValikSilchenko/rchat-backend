import uuid
from datetime import datetime, time
from enum import StrEnum

from pydantic import UUID4, UUID5, BaseModel, Field


class ChatTypeEnum(StrEnum):
    private = "private"
    group = "group"
    channel = "channel"


class UserChatRole(StrEnum):
    admin = "admin"
    owner = "owner"
    member = "member"
    observer = "observer"


class ChatCreate(BaseModel):
    id: UUID4 = Field(default_factory=lambda: uuid.uuid4())
    type: ChatTypeEnum
    name: str | None = None
    avatar_photo_id: UUID4 | None = None
    description: str | None = None
    is_work_chat: bool = False
    allow_messages_from: time | None = None
    allow_messages_to: time | None = None


class Chat(BaseModel):
    id: UUID4
    type: ChatTypeEnum
    name: str | None
    avatar_photo_id: UUID4 | None
    description: str | None
    is_work_chat: bool
    allow_messages_from: time | None
    allow_messages_to: time | None
    created_timestamp: datetime


class ChatParticipantWithInfo(BaseModel):
    id: UUID5
    name: str
    role: UserChatRole
    avatar_photo_id: UUID4 | None
    last_online: datetime | None
    added_by_user: UUID5 | None


class ChatParticipant(BaseModel):
    user_id: UUID5
    role: UserChatRole
    added_by_user: UUID5 | None
