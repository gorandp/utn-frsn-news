from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class NewsBase(BaseModel):
    url: str = Field(min_length=1, max_length=511)
    title: str = Field(min_length=1, max_length=127)
    content: str = Field(min_length=1)
    photo_url: str | None = Field(default=None, max_length=150)


class NewsCreate(NewsBase):
    pass


class NewsShortResponse(NewsBase):
    # Enables ORM mode (read from SQLAlchemy models attributes)
    model_config = ConfigDict(from_attributes=True)

    id: int
    origin_created_at: datetime | None = None


class NewsResponse(NewsBase):
    # Enables ORM mode (read from SQLAlchemy models attributes)
    model_config = ConfigDict(from_attributes=True)

    id: int
    response_elapsed_seconds: float | None = None
    parse_elapsed_seconds: float | None = None
    origin_created_at: datetime | None = None
    indexed_at: datetime
    inserted_at: datetime
