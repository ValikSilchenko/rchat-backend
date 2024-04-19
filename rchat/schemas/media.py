from datetime import datetime
from enum import StrEnum

from pydantic import UUID4, BaseModel


class MediaTypeEnum(StrEnum):
    photo = "photo"
    video = "video"
    video_msg = "video_msg"
    audio = "audio"
    audio_msg = "audio_msg"


class Media(BaseModel):
    id: UUID4
    type: MediaTypeEnum
    size_bytes: int
    extension: str
    created_timestamp: datetime
