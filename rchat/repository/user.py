import uuid
from hashlib import sha256
from secrets import token_hex
from typing import Optional

from asyncpg import Pool
from pydantic import UUID3, UUID4, UUID5, BaseModel

from rchat.schemas.models import User


class UserFind(BaseModel):
    public_id: str
    avatar_url: str | None = None


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
        self, first_name: str, public_id: str, password: str, email: str
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
                "id",
                "first_name",
                "public_id",
                "password",
                "email",
                "user_salt"
            ) values ($1, $2, $3, $4, $5, $6)
            on conflict do nothing
            returning *
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(
                sql,
                user_id,
                first_name,
                public_id,
                encrypted_password,
                email,
                user_salt,
            )

        if not row:
            return

        return User(**dict(row))

    async def find_users_by_public_id(
        self, match_str: str, except_user_id: UUID4 | None = None
    ) -> list[UserFind]:
        """
        Возвращает пользователей, подходящих под поисковую строку.
        Пользователи возвращаются в порядке наибольшего совпадения.
        :param match_str: поисковая строка
        :param except_user_id: id пользователя,
         которого нужно исключить из результатов поиска,
         позволяет исключить поиск самого себя в том числе
        :return: список найденных пользователей,
         для каждого пользователя возвращается его public_id и аватар
        """
        sql = f"""
            select "public_id" from "user"
            where "public_id" like '@%' || $1 || '%'
            and {'"id" <> $2' if except_user_id else True}
            order by
            case
                when "public_id" like '@' || $1 then 1
                when "public_id" like '@' || $1 || '%' then 2
                when "public_id" like '@%' || $1 then 4
                else 3
            end
        """
        if except_user_id:
            params = [match_str, except_user_id]
        else:
            params = [match_str]

        async with self._db.acquire() as c:
            rows = await c.fetch(sql, *params)

        return [UserFind(**dict(row)) for row in rows]

    async def update_user_info(
        self,
        user_id: UUID5,
        public_id: str,
        first_name: str,
        last_name: str | None,
        avatar_photo_id: UUID4 | None,
        profile_status: str | None,
        profile_bio: str | None,
    ):
        sql = """
            update "user"
            set
                "public_id" = $2,
                "first_name" = $3,
                "last_name" = $4,
                "avatar_photo_id" = $5,
                "profile_status" = $6,
                "profile_bio" = $7
            where "id" = $1
        """
        async with self._db.acquire() as c:
            await c.execute(
                sql,
                user_id,
                public_id,
                first_name,
                last_name,
                avatar_photo_id,
                profile_status,
                profile_bio,
            )
