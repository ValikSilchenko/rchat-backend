from datetime import datetime

from pydantic import BaseModel, UUID4, UUID5

from rchat.schemas.models import Message, MessageTypeEnum


class CreateMessageBody(BaseModel):
    chat_id: UUID4 | None = None
    user_public_id: str | None = None
    message_text: str | None = None
    sender_user_id: UUID5 | None = None
    reply_to_message_id: UUID4 | None = None
    forwarded_message_id: UUID4 | None = None
    is_silent: bool = False


class MessageSender(BaseModel):
    user_id: UUID5 | None = None
    chat_id: UUID4 | None = None
    name: str
    avatar_photo_url: str | None = None


class ForeignMessage(BaseModel):
    id: UUID4
    type: MessageTypeEnum
    message_text: str | None = None
    sender: MessageSender


class MessageResponse(BaseModel):
    id: UUID4
    type: MessageTypeEnum
    chat_id: UUID4
    sender: MessageSender
    message_text: str | None = None
    audio_msg_file_link: UUID4 | None = None
    video_msg_file_link: UUID4 | None = None
    reply_to_message: ForeignMessage | None = None
    forwarded_message: ForeignMessage | None = None
    is_silent: bool
    last_edited_at: datetime | None = None
    created_at: datetime
    read_by_users: list[UUID5] = []


class ChatMessagesResponse(BaseModel):
    messages: list[MessageResponse]

