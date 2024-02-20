import uuid
from datetime import datetime, timedelta

from asyncpg import Pool
from pydantic import UUID5, UUID4, BaseModel

from rchat.conf import SESSION_LIFETIME_MIN


class Session(BaseModel):
    id: UUID4
    user_id: UUID5
    ip: str | None = None
    country: str | None
    user_agent: str | None = None
    is_active: bool
    expired_at: datetime
    refresh_id: UUID4
    created_timestamp: datetime | None


class SessionRepository:
    def __init__(self, db: Pool):
        self._db = db

    async def create(
        self,
        user_id: UUID5,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> Session:
        session_data = Session(
            id=uuid.uuid4(),
            user_id=user_id,
            ip=ip,
            user_agent=user_agent,
            country=None,
            is_active=True,
            expired_at=datetime.now()
            + timedelta(minutes=SESSION_LIFETIME_MIN),
            refresh_id=uuid.uuid4(),
            created_timestamp=None,
        )
        model_dump = session_data.model_dump(exclude_none=True)
        field_names = ", ".join(model_dump.keys())
        placeholders = ", ".join(
            [f"${i}" for i in range(1, len(model_dump) + 1)]
        )
        sql = f"""
            insert into "session" ({field_names})
            values ({placeholders})
        """
        async with self._db.acquire() as c:
            await c.execute(sql, *model_dump.values())

        return session_data
