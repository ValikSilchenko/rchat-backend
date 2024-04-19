import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import UUID4, UUID5, BaseModel


class MessageTypeEnum(StrEnum):
    text = "text"
    audio = "audio"
    video = "video"
    created_chat = "created_chat"


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


class MessageCreate(BaseModel):
    id: UUID4 = uuid.uuid4()
    type: MessageTypeEnum
    chat_id: UUID4
    sender_user_id: UUID5 | None = None
    sender_chat_id: UUID4 | None = None
    message_text: str | None = None
    audio_msg_file_id: UUID4 | None = None
    video_msg_file_id: UUID4 | None = None
    reply_to_message: UUID4 | None = None
    forwarded_message: UUID4 | None = None
    is_silent: bool = False
