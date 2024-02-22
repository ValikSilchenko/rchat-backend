from datetime import datetime

from pydantic import UUID4, UUID5
from sqlmodel import SQLModel


class Session(SQLModel):
    id: UUID4
    user_id: UUID5
    ip: str | None = None
    country: str | None = None
    user_agent: str | None
    is_active: bool
    expired_at: datetime
    refresh_id: UUID4
    created_timestamp: datetime | None


class User(SQLModel):
    id: UUID5
    public_id: str
    password: str
    email: str
    user_salt: str
    created_timestamp: datetime
