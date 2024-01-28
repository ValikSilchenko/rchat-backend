from datetime import datetime

from sqlmodel import SQLModel
from pydantic import BaseModel, UUID5, Field, UUID4


class Session(SQLModel):
    id: UUID4
    user_id: UUID5
    ip: str | None = None
    user_agent: str | None = None
    is_active: bool
    country: str | None
    created_timestamp: datetime


class User(SQLModel):
    id: UUID5
    public_id: str
    password: str
    email: str
    user_salt: str
    created_timestamp: datetime


class AuthBody(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    token: str


class CreateUserData(BaseModel):
    public_id: str = Field(min_length=3)
    password: str = Field(min_length=7)
    email: str = Field(pattern=(r"([A-Za-z0-9]+[.-_])"
                                r"*[A-Za-z0-9]+@[A-Za-z0-9-]"
                                r"+(\.[A-Z|a-z]{2,})+")
                       )
