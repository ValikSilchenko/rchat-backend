from datetime import datetime

from sqlmodel import SQLModel
from pydantic import UUID3, BaseModel, UUID1, UUID5


class Session(SQLModel):
    id: str
    user_id: UUID5
    ip: str | None = None
    user_agent: str | None = None
    is_active: bool
    country: str | None
    created_timestamp: datetime


class User(SQLModel):
    id: UUID5
    login: str
    password: str
    created_timestamp: datetime


class AuthBody(BaseModel):
    login: str
    password: str