import uuid
from datetime import datetime
from typing import Optional

from asyncpg import Pool
from pydantic import UUID4, UUID5, BaseModel

from rchat.schemas.models import Chat


class ChatParticipant(BaseModel):
    chat_id: UUID4
    user_id: UUID5
    is_chat_owner: bool
    last_available_message: UUID4 | None
    created_timestamp: datetime


class ChatRepository:
    def __init__(self, db: Pool):
        self._db = db

    async def create_chat(
            self,
            chat_type: str,
            chat_name: str | None = None,
            description: str | None = None,
    ) -> Chat:
        chat_id = uuid.uuid4()
        sql = """
            insert into "chat" (id, type, name, description)
            values ($1, $2, $3, $4)
            returning *
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(sql, chat_id, chat_type, chat_name, description)

        return Chat(**dict(row))

    async def add_chat_participant(self, chat_id: UUID4, user_id: UUID5):
        sql = f"""
            insert into "chat_user" (chat_id, user_id)
            values ($1, $2)
        """
        async with self._db.acquire() as c:
            await c.execute(sql, chat_id, user_id)

    async def get_by_id(self, chat_id: UUID4) -> Optional[Chat]:
        sql = """
            select * from "chat" where "id" = $1
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(sql, chat_id)

        if not row:
            return

        return Chat(**dict(row))

    async def get_chat_participants(self, chat_id: UUID4) -> list[ChatParticipant]:
        sql = """
            select * from "chat_user" where "chat_id" = $1
        """
        async with self._db.acquire() as c:
            rows = await c.fetch(sql, chat_id)

        return [ChatParticipant(**dict(row)) for row in rows]
