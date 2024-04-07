from asyncpg import Pool


class MessageRepository:
    def __init__(self, db: Pool):
        self._db = db

