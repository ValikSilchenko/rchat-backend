import uuid

from asyncpg import Pool
from pydantic import UUID3
from secrets import token_hex
from hashlib import sha256

from rchat.views.auth.models import User


class UserRepository:
    def __init__(self, db: Pool):
        self._db = db

    async def get_by_id(self, id_: UUID3) -> User | None:
        sql = """
            select * from "user"
            where "id" = $1
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(sql, id_)

        if not row:
            return

        return User(**dict(row))

    async def get_by_email(self, email: str):
        sql = """
            select * from "user"
            where "email" = $1
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(sql, email)

        if not row:
            return

        return User(**dict(row))

    async def get_by_public_id(self, public_id: str) -> User | None:
        sql = """
            select * from "user"
            where "public_id" = $1
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(sql, public_id)

        if not row:
            return

        return User(**dict(row))

    async def create(self, public_id: str, password: str, email: str):
        user_id = uuid.uuid5(uuid.NAMESPACE_DNS, public_id)
        user_salt = token_hex(16)

        encrypted_password = sha256(
            string=(password + user_salt).encode()
        ).hexdigest()
        sql = """
            insert into "user" (
                "id", "public_id", "password", "email", "user_salt"
            ) values ($1, $2, $3, $4, $5)
            on conflict do nothing
            returning *
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(
                sql, user_id, public_id, encrypted_password, email, user_salt
            )

        if not row:
            return

        return User(**dict(row))
