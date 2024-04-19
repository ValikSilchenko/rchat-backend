from datetime import datetime

from pydantic import UUID4, UUID5, BaseModel


class User(BaseModel):
    id: UUID5
    public_id: str
    password: str
    email: str
    user_salt: str
    first_name: str
    last_name: str | None
    avatar_photo_id: UUID4 | None
    profile_status: str | None
    profile_bio: str | None
    created_timestamp: datetime


class UserFind(BaseModel):
    id: UUID5
    public_id: str
    avatar_photo_id: UUID4 | None
