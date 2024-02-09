from datetime import datetime
from enum import StrEnum

from sqlmodel import SQLModel
from pydantic import BaseModel, UUID5, Field, UUID4


class Session(SQLModel):
    id: UUID4
    user_id: UUID5
    ip: str | None = None
    country: str | None
    user_agent: str | None = None
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


class LoginTypeEnum(StrEnum):
    email = "email"
    public_id = "public_id"


class AuthBody(BaseModel):
    login: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str


class UserDataPatternEnum(StrEnum):
    public_id = "@[A-Za-z_]+[A-Za-z0-9_.]*"
    email = (
        r"([A-Za-z0-9]+[.-_])"
        r"*[A-Za-z0-9]+@[A-Za-z0-9-]"
        r"+(\.[A-Z|a-z]{2,})+"
    )


class CreateUserData(BaseModel):
    public_id: str = Field(min_length=4, pattern=UserDataPatternEnum.public_id)
    password: str = Field(min_length=7)
    email: str = Field(pattern=UserDataPatternEnum.email)
