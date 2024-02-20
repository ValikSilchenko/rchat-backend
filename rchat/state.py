from asyncpg import create_pool
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel

from rchat.conf import DATABASE_DSN, MIGRATIONS_DATABASE_DSN
from rchat.repository.session import SessionRepository
from rchat.repository.user import UserRepository


class AppState:
    def __init__(self):
        self._db = None
        self._user_repo = None
        self._session_repo = None

    async def startup(self):
        self._db = await create_pool(dsn=DATABASE_DSN)

        self._user_repo = UserRepository(db=self._db)
        self._session_repo = SessionRepository(db=self._db)

    async def shutdown(self):
        if self._db:
            await self._db.close()

    async def init_migrations(self):
        pass

    @property
    def user_repo(self) -> UserRepository:
        assert self._user_repo
        return self._user_repo

    @property
    def session_repo(self) -> SessionRepository:
        assert self._session_repo
        return self._session_repo


app_state = AppState()
