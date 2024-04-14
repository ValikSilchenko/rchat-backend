from datetime import datetime

from pydantic import BaseModel, UUID4, UUID5

from rchat.schemas.models import Message, MessageTypeEnum


class CreateMessageBody(BaseModel):
    """
    Модель для запроса создания сообщения.
    """
    chat_id: UUID4 | None = None
    other_user_public_id: str | None = None
    message_text: str | None = None
    reply_to_message_id: UUID4 | None = None
    forwarded_message_id: UUID4 | None = None
    is_silent: bool = False


class MessageSender(BaseModel):
    """
    Модель отправителя сообщения.

    Отправитель может быть:
     - пользователем (chat_id = None),
     - чатом (user_id = None).
    """
    user_id: UUID5 | None = None
    chat_id: UUID4 | None = None
    name: str
    avatar_photo_url: str | None = None


class ForeignMessage(BaseModel):
    """
    Модель пересланного сообщения или отвеченного сообщения.
    """
    id: UUID4
    type: MessageTypeEnum
    message_text: str | None = None
    sender: MessageSender


class MessageResponse(BaseModel):
    """
    Модель сообщения для метода получения списка сообщения.
    """
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

