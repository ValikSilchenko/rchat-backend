from asyncpg import create_pool

from rchat.conf import DATABASE_DSN
from rchat.repository.chat import ChatRepository
from rchat.repository.geoip import GeoIPRepository
from rchat.repository.media import MediaRepository
from rchat.repository.message import MessageRepository
from rchat.repository.session import SessionRepository
from rchat.repository.user import UserRepository


class AppState:
    def __init__(self):
        self._db = None
        self._engine = None
        self._user_repo = None
        self._session_repo = None
        self._geoip_repo = None
        self._media_repo = None
        self._chat_repo = None
        self._message_repo = None

    async def startup(self):
        self._db = await create_pool(dsn=DATABASE_DSN)

        self._user_repo = UserRepository(db=self._db)
        self._session_repo = SessionRepository(db=self._db)
        self._geoip_repo = GeoIPRepository(db=self._db)
        self._media_repo = MediaRepository(db=self._db)
        self._chat_repo = ChatRepository(db=self._db)
        self._message_repo = MessageRepository(db=self._db)

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

    @property
    def geoip_repo(self) -> GeoIPRepository:
        assert self._geoip_repo
        return self._geoip_repo

    @property
    def media_repo(self) -> MediaRepository:
        assert self._media_repo
        return self._media_repo

    @property
    def chat_repo(self) -> ChatRepository:
        assert self._chat_repo
        return self._chat_repo

    @property
    def message_repo(self) -> MessageRepository:
        assert self._message_repo
        return self._message_repo


app_state = AppState()
