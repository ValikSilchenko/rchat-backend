from typing import Optional

from asyncpg import Pool
from pydantic import UUID4, UUID5

from rchat.repository.helpers import build_model
from rchat.schemas.chat import Chat, ChatCreate, ChatTypeEnum, UserChatRole


class ChatRepository:
    def __init__(self, db: Pool):
        self._db = db

    async def create_chat(self, create_model: ChatCreate) -> Chat:
        """
        Создаёт чат в БД.
        """
        model_build = build_model(create_model)
        sql = f"""
            insert into "chat" ({model_build.field_names})
            values ({model_build.placeholders})
            returning *
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(sql, *model_build.values)

        return Chat(**dict(row))

    async def add_chat_participant(
        self,
        chat_id: UUID4,
        user_id: UUID5,
        added_by_user: UUID5 | None = None,
        role: UserChatRole = UserChatRole.member,
        last_available_message: UUID4 | None = None,
    ) -> None:
        """
        Добавляет пользователя в чат как участника.
        """
        sql = """
            insert into "chat_user" (
                "chat_id",
                "user_id",
                "added_by_user",
                "role",
                "last_available_message"
            )
            values ($1, $2, $3, $4, $5)
        """
        async with self._db.acquire() as c:
            await c.execute(
                sql,
                chat_id,
                user_id,
                added_by_user,
                role,
                last_available_message,
            )

    async def get_by_id(self, chat_id: UUID4) -> Optional[Chat]:
        """
        Получает чат по его id, если такой есть.
        """
        sql = """
            select * from "chat" where "id" = $1
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(sql, chat_id)

        if not row:
            return

        return Chat(**dict(row))

    async def get_chat_participant_users(self, chat_id: UUID4) -> list[UUID5]:
        """
        Получает список id пользователей чата.
        """
        sql = """
            select "user_id" from "chat_user" where "chat_id" = $1
        """
        async with self._db.acquire() as c:
            rows = await c.fetch(sql, chat_id)

        return [UUID5(str(row["user_id"])) for row in rows]

    async def get_user_chats(self, user_id: UUID5) -> list[Chat]:
        """
        Получает список чатов пользователя,
        отсортированных по времени последнего сообщения в этих чатах.
        """
        sql = """
            select
                "chat"."id",
                "chat"."type",
                "chat"."name",
                "chat"."created_by",
                "chat"."avatar_photo_id",
                "chat"."description",
                "chat"."is_work_chat",
                "chat"."allow_messages_from",
                "chat"."allow_messages_to",
                "chat"."created_timestamp",
                max(m."created_timestamp") as last_message_timestamp
            from "chat"
            left join "chat_user" on "chat"."id" = "chat_user"."chat_id"
            left join "message" m on "chat"."id" = m."chat_id"
            where "user_id" = $1
            group by
                "chat"."id",
                "chat"."type",
                "chat"."name",
                "chat"."created_by",
                "chat"."avatar_photo_id",
                "chat"."description",
                "chat"."is_work_chat",
                "chat"."allow_messages_from",
                "chat"."allow_messages_to",
                "chat"."created_timestamp"
            order by last_message_timestamp desc
        """
        async with self._db.acquire() as c:
            rows = await c.fetch(sql, user_id)

        return [Chat(**dict(row)) for row in rows]

    async def get_private_chat_with_users(
        self, users_id_list: list[UUID5]
    ) -> Optional[Chat]:
        """
        Получает чат типа private по его участникам, если такой есть.
        """
        sql = f"""
            select distinct
                c.id,
                c.type,
                c.name,
                c.avatar_photo_id,
                c.description,
                c.created_timestamp
            from "chat_user" cu1
                left join "chat_user" cu2 on cu1."chat_id" = cu2."chat_id"
                left join "chat" c on c."id" = cu1."chat_id"
            where
                cu1."user_id" != cu2."user_id"
                and cu1."user_id" = any($1) and cu2."user_id" = any($1)
                and c."type" = '{ChatTypeEnum.private}'
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(sql, users_id_list)

        if not row:
            return

        return Chat(**dict(row))


