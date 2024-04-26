from typing import Optional

from asyncpg import Pool
from pydantic import UUID4, UUID5

from rchat.repository.helpers import build_model
from rchat.schemas.message import Message, MessageCreate


class MessageRepository:
    def __init__(self, db: Pool):
        self._db = db

    async def create_message(self, message: MessageCreate) -> Message:
        """
        Добавляет сообщение в БД на основе модели для создания.
        """
        model_build = build_model(message)
        sql = f"""
            insert into "message" ({model_build.field_names})
            values ({model_build.placeholders})
            returning *
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(sql, *model_build.values)

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

    async def mark_message_as_read(
        self, message_id: UUID4, read_by_user: UUID5
    ) -> bool:
        """
        Помечает сообщение как прочитанное.
        """
        sql = """
            insert into "message_read" (message_id, user_id)
            values ($1, $2)
            on conflict do nothing
            returning true
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(sql, message_id, read_by_user)

        return bool(row)

    async def get_read_user_id_list(self, message_id: UUID4) -> list[UUID5]:
        sql = """
            select "user_id" from "message_read"
            where "message_id" = $1
        """
        async with self._db.acquire() as c:
            rows = await c.fetch(sql, message_id)

        return [UUID5(str(row["user_id"])) for row in rows]

    async def get_unread_messages_before_for_user(
        self, chat_id: UUID4, before_message_id: UUID4, user_id: UUID5
    ) -> list[UUID4]:
        sql = """
            select "id" from "message"
            where "chat_id" = $1
            and ("sender_user_id" is null or "sender_user_id" <> $3)
            and "created_timestamp" < (
                select "created_timestamp" from "message"
                where "id" = $2
            )
        """
        async with self._db.acquire() as c:
            rows = await c.fetch(sql, chat_id, before_message_id, user_id)

        return [UUID5(str(row["id"])) for row in rows]
