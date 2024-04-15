from asyncpg import Pool
from pydantic import UUID4


class MediaRepository:
    def __init__(self, db: Pool):
        self._db = db

    def get_media_url(self, id_: UUID4):
        return ""
