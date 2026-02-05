from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select

from ..database_models import News
from ..cloudflare_images import CloudflareImages
from .messenger.telegram import Telegram
from .scraper.feed import HistoricFeed
from .scraper.news import NewsReader
from .messenger.message_formatter import (
    build_message,
    build_message_header,
)


async def index_scraper(session: Session):
    # Get latest URL from DB
    latest_url = session.execute(
        select(News.url).order_by(News.origin_created_at.desc()).limit(1)
    ).scalar_one_or_none()

    # Get news URLs from historic feed
    historic_feed = HistoricFeed()
    news_urls = await historic_feed.get_urls(latest_url=latest_url)

    # Check existing URLs in DB
    existing_urls: list[str] = []
    for batch in range(0, len(news_urls), 100):
        batch_urls = news_urls[batch : batch + 100]
        existing_urls.extend(
            session.execute(
                select(News.url).where(News.url.in_([u[0] for u in batch_urls]))
            )
            .scalars()
            .all()
        )

    # Filter out existing URLs
    return [u for u in news_urls if u[0] not in existing_urls]


async def main_scraper(
    session: Session,
    news_url: str,
    photo_url: str,
    indexed_at: datetime,
):
    news_reader = NewsReader()
    news_data = await news_reader.read_news(news_url)

    image_id = None
    image_data = await news_reader.fetch_image(photo_url)
    if image_data:
        news_origin_id = news_url.rsplit("=", 1)[-1]
        image_origin_filename = photo_url.rsplit("/", 1)[-1]
        image_filename = f"utn-frsn-news-photo-{news_origin_id}-{image_origin_filename}"
        cloudflare_images = CloudflareImages()
        image_id = await cloudflare_images.upload(
            image_filename,
            image_data,
        )

    # Insert news into DB
    news_entry = News(
        url=news_data["url"],
        title=news_data["title"],
        content=news_data["content"],
        photo_id=image_id,
        response_elapsed_seconds=news_data["response_elapsed_seconds"],
        parse_elapsed_seconds=news_data["parse_elapsed_seconds"],
        origin_created_at=news_data["origin_created_at"],
        indexed_at=indexed_at,
    )
    session.add(news_entry)
    session.commit()
    session.refresh(news_entry)

    return news_entry.id


async def messenger(
    session: Session,
    news_id: int,
):
    news_entry = session.get(News, news_id)
    if not news_entry:
        raise ValueError(f"News with ID {news_id} not found")
    photo_url = None
    if news_entry.photo_id:
        photo_url = CloudflareImages.get_public_url(news_entry.photo_id)

    message = build_message(news_entry)
    message_header = build_message_header(news_entry)
    telegram = Telegram()
    if photo_url:
        r = await telegram.send_photo(news_id, photo_url, message_header)
        if r is False:
            raise ValueError("Failed to send photo via Telegram")
    r = await telegram.send_message(news_id, message)
    if r is False:
        raise ValueError("Failed to send message via Telegram")
