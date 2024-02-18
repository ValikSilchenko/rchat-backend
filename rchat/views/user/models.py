from pydantic import BaseModel

from rchat.repository.user import UserFind


class FindUsersResponse(BaseModel):
    users: list[UserFind]