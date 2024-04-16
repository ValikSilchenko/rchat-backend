from enum import StrEnum

from pydantic import UUID4, BaseModel, Field

from rchat.repository.user import UserFind
from rchat.views.auth.models import UserDataPatternEnum


class FindUsersResponse(BaseModel):
    users: list[UserFind]


class ProfileResponse(BaseModel):
    public_id: str
    email: str
    first_name: str
    last_name: str | None
    avatar_photo_url: str | None
    profile_status: str | None
    profile_bio: str | None


class ProfileUpdateStatusEnum(StrEnum):
    public_id_already_taken = "public_id_already_taken"
    invalid_photo_id = "invalid_photo_id"


class ProfileUpdateBody(BaseModel):
    public_id: str = Field(
        min_length=4, max_length=32, pattern=UserDataPatternEnum.public_id
    )
    first_name: str = Field(min_length=2, max_length=32)
    last_name: str | None = Field(min_length=2, max_length=32)
    avatar_photo_id: UUID4 | None
    profile_status: str | None = Field(max_length=64)
    profile_bio: str | None = Field(max_length=512)
