from asyncpg import create_pool

from rchat.repository.session import SessionRepository
from rchat.repository.user import UserRepository


class AppState:
    def __init__(self):
        pass

    async def startup(self):
        self._db = await create_pool(dsn="postgresql://postgres:postgres@localhost:1946/postgres")

        self._user_repo = UserRepository(db=self._db)
        self._session_repo = SessionRepository(db=self._db)

    async def shutdown(self):
        if self._db:
            await self._db.close()

    @property
    def user_repo(self) -> UserRepository:
        assert self._user_repo
        return self._user_repo

    @property
    def session_repo(self) -> SessionRepository:
        assert self._session_repo
        return self._session_repo


app_state = AppState()
