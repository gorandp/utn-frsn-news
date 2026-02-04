from __future__ import annotations

from datetime import datetime, UTC
from typing import Any

from sqlalchemy import Integer, Float, String, Text
from sqlalchemy.types import TypeDecorator
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase

from .cloudflare_images import CloudflareImages


class DateTimeString(TypeDecorator[datetime]):
    impl = String
    cache_ok = True

    def process_bind_param(
        self, value: str | datetime | None | Any, dialect: Any
    ) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            return value
        if isinstance(value, datetime):
            return value.isoformat()
        raise ValueError(f"Cannot convert {type(value)} to datetime string")

    def process_result_value(self, value: str | None, dialect: Any) -> datetime | None:
        if value is None:
            return None
        return datetime.fromisoformat(value)


class Base(DeclarativeBase):
    pass


class News(Base):
    __tablename__ = "news"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    url: Mapped[str] = mapped_column(String(511), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(127))
    content: Mapped[str] = mapped_column(Text)
    photo_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    response_elapsed_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    parse_elapsed_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    origin_created_at: Mapped[datetime | None] = mapped_column(
        DateTimeString,
        nullable=True,
    )
    indexed_at: Mapped[datetime] = mapped_column(
        DateTimeString,
        default=lambda: datetime.now(UTC),
    )
    inserted_at: Mapped[datetime] = mapped_column(
        DateTimeString,
        default=lambda: datetime.now(UTC),
    )

    @property
    def photo_url(self) -> str | None:
        if self.photo_id is None:
            return None
        return CloudflareImages.get_public_url(self.photo_id)
