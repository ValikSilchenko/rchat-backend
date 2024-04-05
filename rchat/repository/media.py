from asyncpg import Pool


class MediaRepository:
    def __init__(self, db: Pool):
        self._db = db
