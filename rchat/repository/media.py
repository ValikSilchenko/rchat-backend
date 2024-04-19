from typing import Optional

from asyncpg import Pool
from pydantic import UUID4

from rchat.schemas.media import Media


class MediaRepository:
    def __init__(self, db: Pool):
        self._db = db

    async def get_media_by_id(self, id_: UUID4) -> Optional[Media]:
        sql = """
            select * from "media"
            where "id" = $1
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(sql, id_)

        if not row:
            return

        return Media(**dict(row))

    def get_media_url(self, id_: UUID4):
        return ""
