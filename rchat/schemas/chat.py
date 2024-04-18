from datetime import datetime
from enum import StrEnum

from pydantic import UUID4, BaseModel


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
