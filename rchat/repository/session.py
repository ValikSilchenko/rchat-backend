import uuid
from datetime import datetime, timedelta
from typing import Optional

from asyncpg import Pool
from pydantic import UUID5, UUID4, BaseModel

from rchat.conf import SESSION_LIFETIME_MIN
from rchat.schemas.models import Session


class SessionCreate(BaseModel):
    id: UUID4
    user_id: UUID5
    ip: str | None = None
    country: str | None = None
    user_agent: str | None
    is_active: bool
    expired_at: datetime
    refresh_id: UUID4


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
            expired_at=datetime.now()
            + timedelta(minutes=SESSION_LIFETIME_MIN),
            refresh_id=uuid.uuid4(),
        )
        model_dump = session_data.model_dump(exclude_none=True)
        field_names = ", ".join(model_dump.keys())
        placeholders = ", ".join(
            [f"${i}" for i in range(1, len(model_dump) + 1)]
        )
        sql = f"""
            insert into "session" ({field_names})
            values ({placeholders})
            returning *
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(sql, *model_dump.values())

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
