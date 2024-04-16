from datetime import datetime
from enum import StrEnum

from pydantic import UUID4, UUID5, BaseModel


class Session(BaseModel):
    id: UUID4
    user_id: UUID5
    ip: str | None = None
    country: str | None = None
    user_agent: str | None
    is_active: bool
    device_fingerprint: str | None
    created_timestamp: datetime


class User(BaseModel):
    id: UUID5
    public_id: str
    password: str
    email: str
    user_salt: str
    first_name: str
    last_name: str | None
    avatar_photo_id: UUID4 | None
    profile_status: str | None
    profile_bio: str | None
    created_timestamp: datetime


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


class MessageTypeEnum(StrEnum):
    text = "text"
    audio = "audio"
    video = "video"


class Message(BaseModel):
    id: UUID4
    type: MessageTypeEnum
    chat_id: UUID4
    sender_user_id: UUID5 | None
    sender_chat_id: UUID4 | None
    message_text: str | None
    audio_msg_file_id: UUID4 | None
    video_msg_file_id: UUID4 | None
    reply_to_message: UUID4 | None
    forwarded_message: UUID4 | None
    is_silent: bool
    last_edited_at: datetime | None
    created_timestamp: datetime


class MediaTypeEnum(StrEnum):
    photo = "photo"
    video = "video"
    video_msg = "video_msg"
    audio = "audio"
    audio_msg = "audio_msg"


class Media(BaseModel):
    id: UUID4
    type: MediaTypeEnum
    size_bytes: int
    extension: str
    created_timestamp: datetime
