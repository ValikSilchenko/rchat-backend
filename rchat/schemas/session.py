from datetime import datetime

from pydantic import UUID4, UUID5, BaseModel


class Session(BaseModel):
    id: UUID4
    user_id: UUID5
    ip: str | None = None
    country: str | None = None
    user_agent: str | None
    is_active: bool
    device_fingerprint: str
    created_timestamp: datetime


class SessionCreate(BaseModel):
    id: UUID4
    user_id: UUID5
    ip: str | None = None
    user_agent: str | None
    is_active: bool
    device_fingerprint: str
