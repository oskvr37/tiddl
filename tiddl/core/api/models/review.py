from datetime import datetime
from pydantic import BaseModel


class AlbumReview(BaseModel):
    source: str
    lastUpdated: datetime
    summary: str
