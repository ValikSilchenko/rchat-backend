from enum import StrEnum

from email_validator import validate_email
from pydantic import BaseModel, EmailStr, Field, field_validator


class AuthBody(BaseModel):
    login: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str


class UserDataPatternEnum(StrEnum):
    public_id = "@[A-Za-z_]+[A-Za-z0-9_.]*"


class CreateUserData(BaseModel):
    first_name: str = Field(min_length=2, max_length=32)
    public_id: str = Field(
        min_length=4, max_length=32, pattern=UserDataPatternEnum.public_id
    )
    password: str = Field(min_length=7, max_length=64)
    email: EmailStr = Field(max_length=64)

    @field_validator("email", mode="before")
    def validate_email(cls, email_str: EmailStr):
        validate_email(email_str, check_deliverability=True)
        return email_str
