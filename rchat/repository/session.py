import uuid
from typing import Optional

from asyncpg import Pool
from pydantic import UUID4, UUID5, BaseModel

from rchat.repository.helpers import build_model
from rchat.schemas.models import Session


class SessionCreate(BaseModel):
    id: UUID4
    user_id: UUID5
    ip: str | None = None
    country: str | None = None
    user_agent: str | None
    is_active: bool


class SessionRepository:
    def __init__(self, db: Pool):
        self._db = db

    async def create(
        self,
        user_id: UUID5,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> Session:
        """
        Создаёт сессию пользователя
        :param user_id: uuid пользователя
        :param ip: ip-адресс пользователя (при наличии)
        :param user_agent: user_agent, с которого отправлен запрос
         (при наличии)
        :return: Модель сессии пользователя
        """
        session_data = SessionCreate(
            id=uuid.uuid4(),
            user_id=user_id,
            ip=ip,
            user_agent=user_agent,
            country=None,
            is_active=True,
        )
        sql_build = build_model(model=session_data, exclude_none=True)
        sql = f"""
            insert into "session" ({sql_build.field_names})
            values ({sql_build.placeholders})
            returning *
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(sql, *sql_build.values)

        return Session(**dict(row))

    async def get_by_id(self, id_: UUID4) -> Optional[Session]:
        """
        Возвращает сессию пользователя по id сессии.
        :return: Модель сессии пользователя
        """
        sql = """
            select * from "session"
            where "id" = $1
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(sql, id_)

        if not row:
            return

        return Session(**dict(row))

    async def delete_session(self, session_id: UUID4) -> bool:
        """
        Удаляет сессию пользователя по id сессии.
        :return: True в случае успешного удаления,
         False если сессия не найдена.
        """
        sql = """
            delete from "session" where "id" = $1
            returning true
        """
        async with self._db.acquire() as c:
            result = await c.fetchrow(sql, session_id)

        return bool(result)
