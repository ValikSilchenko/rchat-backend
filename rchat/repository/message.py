from typing import Optional

from asyncpg import Pool
from pydantic import UUID4

from rchat.repository.helpers import build_model
from rchat.schemas.message import Message, MessageCreate


class MessageRepository:
    def __init__(self, db: Pool):
        self._db = db

    async def create_message(self, message: MessageCreate) -> Message:
        """
        Добавляет сообщение в БД на основе модели для создания.
        """
        sql_build = build_model(message)
        sql = f"""
            insert into "message" ({sql_build.field_names})
            values ({sql_build.placeholders})
            returning *
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(sql, *sql_build.values)

        return Message(**dict(row))

    async def get_chat_messages(
        self, chat_id: UUID4, last_order_id: int, limit: int
    ) -> list[Message]:
        """
        Получает список сообщений чата отсортированных по дате создания.
        """
        sql = """
            select * from "message"
            where "chat_id" = $1 and "order_id" > $2
            order by "created_timestamp" limit $3
        """
        async with self._db.acquire() as c:
            rows = await c.fetch(sql, chat_id, last_order_id, limit)

        return [Message(**dict(row)) for row in rows]

    async def get_by_id(self, id_: UUID4) -> Optional[Message]:
        """
        Получает сообщение по его id.
        """
        sql = """
            select * from "message"
            where "id" = $1
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(sql, id_)

        if not row:
            return

        return Message(**dict(row))

    async def get_last_chat_message(self, chat_id: UUID4) -> Optional[Message]:
        sql = """
            select * from "message" m1
            where "chat_id" = $1 and "created_timestamp" = (
                select max("created_timestamp") from "message" m2
                where m2."chat_id" = $1
            )
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(sql, chat_id)

        if not row:
            return

        return Message(**dict(row))
