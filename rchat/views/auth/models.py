from enum import StrEnum

from email_validator import validate_email
from pydantic import BaseModel, EmailStr, Field, field_validator


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
