from datetime import datetime
from enum import StrEnum

from email_validator import validate_email
from pydantic import UUID4, UUID5, BaseModel, EmailStr, Field, field_validator
from sqlmodel import SQLModel


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
    email: EmailStr
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


class CreateUserData(BaseModel):
    public_id: str = Field(min_length=4, pattern=UserDataPatternEnum.public_id)
    password: str = Field(min_length=7)
    email: EmailStr

    @field_validator("email", mode="before")
    def validate_email(cls, email_str: EmailStr):
        validate_email(email_str, check_deliverability=True)
        return email_str
