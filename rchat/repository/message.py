import uuid

from asyncpg import Pool
from pydantic import UUID4, UUID5, BaseModel

from rchat.repository.helpers import build_model
from rchat.schemas.models import Message, MessageTypeEnum


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
    is_silent: bool


class MessageRepository:
    def __init__(self, db: Pool):
        self._db = db

    async def create_message(self, message: MessageCreate) -> Message:
        sql_build = build_model(message)
        sql = f"""
            insert into "message" ({sql_build.field_names})
            values ({sql_build.placeholders})
            returning *
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(sql, *sql_build.values)

        return Message(**dict(row))
