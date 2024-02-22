from datetime import datetime

from pydantic import UUID4, UUID5
from sqlalchemy import VARCHAR, DateTime, Column, func
from sqlmodel import Field

from rchat.schemas.models import Session, User


class SessionSchema(Session, table=True):
    __tablename__ = "session"

    id: UUID4 = Field(primary_key=True)
    ip: str | None = Field(sa_type=VARCHAR(15), default=None)
    country: str | None = Field(sa_type=VARCHAR(32))
    user_agent: str | None = Field(sa_type=VARCHAR(64))
    created_timestamp: datetime = Field(
        sa_column=Column(DateTime, nullable=False, server_default=func.now())
    )


class UserSchema(User, table=True):
    __tablename__ = "user"

    id: UUID5 = Field(primary_key=True)
    public_id: str = Field(sa_type=VARCHAR(32), unique=True)
    password: str = Field(sa_type=VARCHAR(64))
    email: str = Field(sa_type=VARCHAR(128))
    user_salt: str = Field(sa_type=VARCHAR(32), unique=True)
    created_timestamp: datetime = Field(
        sa_column=Column(DateTime, nullable=False, server_default=func.now())
    )
