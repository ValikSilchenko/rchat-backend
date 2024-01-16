from asyncpg import Pool
from pydantic import UUID3

from rchat.views.auth.models import User


class UserRepository:
    def __init__(self, db: Pool):
        self._db = db

    async def get_by_id(self, id: UUID3) -> User | None:
        sql = """
            select * from "user"
            where "id" = $1
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(sql, id)

        if not row:
            return

        return User(**dict(row))

    async def get_by_login(self, login: str):
        sql = """
            select * from "user"
            where "login" = $1
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(sql, login)

        if not row:
            return

        return User(**dict(row))
