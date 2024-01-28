import uuid

from asyncpg import Pool
from pydantic import BaseModel, UUID5, UUID4


class SessionCreate(BaseModel):
    id: UUID4
    user_id: UUID5
    ip: str | None = None
    user_agent: str | None = None
    country: str | None = None
    is_active: bool


class SessionRepository:
    def __init__(self, db: Pool):
        self._db = db

    async def create(self, user_id: UUID5, ip: str | None = None, user_agent: str | None = None):
        session_data = SessionCreate(
            id=uuid.uuid4(),
            user_id=user_id,
            ip=ip,
            user_agent=user_agent,
            country=None,
            is_active=True
        )
        model_dump = session_data.model_dump()
        field_names = ", ".join(model_dump.keys())
        placeholders = ", ".join([f"${i}" for i in range(1, len(model_dump) + 1)])
        sql = f"""
            insert into "session" ({field_names})
            values ({placeholders})
        """
        async with self._db.acquire() as c:
            await c.execute(sql, *model_dump.values())

        return session_data
