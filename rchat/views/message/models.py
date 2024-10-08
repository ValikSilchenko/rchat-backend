from datetime import datetime, time
from enum import StrEnum

from pydantic import UUID4, UUID5, BaseModel

from rchat.schemas.chat import ChatTypeEnum
from rchat.schemas.message import MessageTypeEnum


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


class ChatInfo(BaseModel):
    """
    Модель информации о чате, в котором пришло сообщение.
    """

    id: UUID4
    type: ChatTypeEnum
    name: str | None = None
    is_work_chat: bool
    allow_messages_from: time | None
    allow_messages_to: time | None
    avatar_photo_url: str | None = None
    created_at: datetime


class ActionUserParticipant(BaseModel):
    id: UUID5
    first_name: str


class MessageResponse(BaseModel):
    """
    Модель сообщения для метода получения списка сообщения.
    """

    id: UUID4
    type: MessageTypeEnum
    sender: MessageSender
    message_text: str | None = None
    audio_msg_file_link: str | None = None
    video_msg_file_link: str | None = None
    reply_to_message: ForeignMessage | None = None
    forwarded_message: ForeignMessage | None = None
    user_initiated_action: ActionUserParticipant | None = None
    user_involved: ActionUserParticipant | None = None
    is_silent: bool
    last_edited_at: datetime | None = None
    created_at: datetime
    read_by_users: list[UUID5] = []


class ChatMessagesResponse(BaseModel):
    messages: list[MessageResponse]


class NewMessageResponse(MessageResponse):
    chat: ChatInfo


class ChatMessagesStatusEnum(StrEnum):
    chat_not_found = "chat_not_found"
    user_not_in_chat = "user_not_in_chat"


class NewMessageStatusEnum(StrEnum):
    user_not_found = "user_not_found"
    chat_not_found = "chat_not_found"
    no_message_sender_provided = "no_message_sender_provided"
    two_chat_identifiers_provided = "two_chat_identifiers_provided"
    cannot_reply_this_message = "cannot_reply_this_message"
    cannot_forward_this_message = "cannot_forward_this_message"


class ReadMessageBody(BaseModel):
    message_id: UUID4
    chat_id: UUID4


class ReadMessageStatusEnum(StrEnum):
    message_not_found = "message_not_found"
    user_not_in_chat = "user_not_in_chat"
    user_already_read_the_message = "user_already_read_the_message"
    user_cannot_read_own_message = "user_cannot_read_own_message"


class ReadMessageResponse(BaseModel):
    chat_id: UUID4
    message_id: UUID4
    read_by_user: UUID5
