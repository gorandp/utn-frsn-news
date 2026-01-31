from __future__ import annotations

from datetime import datetime, UTC
from typing import Any

from sqlalchemy import Integer, Float, String, Text, ForeignKey
from sqlalchemy.types import TypeDecorator
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase


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

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(String(511), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(127))
    content: Mapped[str] = mapped_column(Text)
    photo_location: Mapped[str | None] = mapped_column(String(63), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(127), nullable=True)
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


class QueuesErrors(Base):
    __tablename__ = "queues_errors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    news_id: Mapped[int | None] = mapped_column(
        ForeignKey("news.id"), index=True, nullable=False
    )
    news_url: Mapped[str | None] = mapped_column(String(511), nullable=True)
    error_message: Mapped[str] = mapped_column(Text)
    queue: Mapped[str] = mapped_column(String(63))
    task_inserted_at: Mapped[datetime] = mapped_column(
        DateTimeString,
        nullable=True,
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTimeString,
        default=lambda: datetime.now(UTC),
    )
