import uuid
from hashlib import sha256
from secrets import token_hex
from typing import Optional

from asyncpg import Pool
from pydantic import UUID3

from rchat.views.auth.models import User


class UserRepository:
    def __init__(self, db: Pool):
        self._db = db

    async def get_by_id(self, id_: UUID3) -> Optional[User]:
        """
        Получает пользователя по его id.
        :return: модель пользователя или None, если пользователь не найден
        """
        sql = """
            select * from "user"
            where "id" = $1
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(sql, id_)

        if not row:
            return

        return User(**dict(row))

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Получает пользователя по его email.
        :return: модель пользователя или None, если пользователь не найден
        """
        sql = """
            select * from "user"
            where "email" = $1
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(sql, email)

        if not row:
            return

        return User(**dict(row))

    async def get_by_public_id(self, public_id: str) -> Optional[User]:
        """
        Получает пользователя по его public_id.
        :return: модель пользователя или None, если пользователь не найден
        """
        sql = """
            select * from "user"
            where "public_id" = $1
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(sql, public_id)

        if not row:
            return

        return User(**dict(row))

    async def create(
        self, public_id: str, password: str, email: str
    ) -> Optional[User]:
        """
        Создаёт нового пользователя в базе.
        :return: модель пользователя
        или None при попытке создания пользователя с существующим public_id
        """
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
