from datetime import datetime

from pydantic import BaseModel


class GeoIPData(BaseModel):
    ip: str
    state: str | None
    country: str | None
    city: str | None
    updated_timestamp: datetime
