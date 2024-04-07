from asyncpg import Pool


class ChatRepository:
    def __init__(self, db: Pool):
        self._db = db
