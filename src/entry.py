from datetime import datetime, UTC
from workers import WorkerEntrypoint  # , Response, Request
from pyodide.ffi import to_js
from sqlalchemy_cloudflare_d1 import create_engine_from_binding  # type: ignore
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import select

import app.constants as cts
from app.logger import LogWrapper, LoggerConfig
from app.database_models import News, Base as DatabaseBaseModel
from app.cloudflare_images import CloudflareImages, CloudflareConfig
from app.cloudflare_queues import QueueScraper, QueueMessenger
from app.scraper.feed import HistoricFeed
from app.scraper.news import NewsReader
from app.messenger.telegram import Telegram
from app.messenger.message_formatter import build_message, build_message_header


# from contextvars import ContextVar
# # ContextVar to handle session context safely
# db_session: ContextVar[Session] = ContextVar("db_session")


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


class EntryLogger(LogWrapper):
    pass


class Default(WorkerEntrypoint):
    def __init__(self, ctx, env):
        super().__init__(ctx, env)
        LoggerConfig.set_level(self.env.LOGGER_LEVEL)
        self.logger = EntryLogger().logger
        engine = create_engine_from_binding(self.env.DB)
        self.SessionLocal = sessionmaker(bind=engine)
        DatabaseBaseModel.metadata.create_all(bind=engine)  # Create tables if not exist
        CloudflareConfig.setup(
            account_id=self.env.CLOUDFLARE_ACCOUNT_ID,
            images_account_hash=self.env.CLOUDFLARE_IMAGES_ACCOUNT_HASH,
            images_api_token=self.env.CLOUDFLARE_IMAGES_API_TOKEN,
        )
        Telegram.setup_config(
            chat_id=cts.TELEGRAM_CHANNEL_PROD
            if self.env.TELEGRAM_CHAT_ENV == "prod"
            else cts.TELEGRAM_CHANNEL_DEBUG,
            telegram_api_key=self.env.TELEGRAM_API_KEY,
            silent_mode=getattr(self.env, "TELEGRAM_SILENT_MODE", "").lower() == "true",
        )

    # Scheduled Worker
    # Index Scraper
    async def scheduled(self, controller, env, ctx):
        self.logger.info("Starting scheduled task")
        with self.SessionLocal() as session:
            news_urls = await index_scraper(session)
            if news_urls:
                tasks = QueueScraper.bulk_new(news_urls)
                for i in range(0, len(tasks), 100):
                    # Max 100 messages per batch
                    batch = tasks[i : i + 100]
                    await self.env.SCRAPER_QUEUE.sendBatch(to_js(batch))
        self.logger.info("Scheduled task completed successfully")

    # Queue Worker
    # Main Scraper and Messenger Worker
    async def queue(
        self,
        batch,
        unknown1: None = None,
        unknown2: None = None,
    ):
        self.logger.info(f"Start batch queue {batch.queue}")
        with self.SessionLocal() as session:
            ## ------> SCRAPER_QUEUE <------ ##
            if batch.queue == "653f3c467afd43278463cb87292d1c97":
                self.logger.info("Processing SCRAPER_QUEUE batch")
                for message in batch.messages:
                    task = QueueScraper.read(message)
                    try:
                        news_id = await main_scraper(
                            session,
                            task.news_url,
                            task.photo_url,
                            datetime.now(UTC),
                        )
                        await self.env.MESSENGER_QUEUE.send(
                            to_js(QueueMessenger.new(news_id))
                        )
                    except Exception as e:
                        self.logger.error(f"[{task.news_url}] Error scraping news: {e}")
                        telegram = Telegram()
                        await telegram.send_message(
                            0,
                            f"[SCRAPER ERROR] [{task.news_url}] Error scraping news: {e}",
                            chat_id=cts.TELEGRAM_CHANNEL_DEBUG,
                        )

            ## ------> MESSENGER_QUEUE <------ ##
            elif batch.queue == "a0f45ea683634af2a991a1dd7379f9eb":
                self.logger.info("Processing MESSENGER_QUEUE batch")
                for message in batch.messages:
                    task = QueueMessenger.read(message)
                    try:
                        self.logger.info(f"News ID to process: {task.news_id}")
                        await messenger(
                            session,
                            task.news_id,
                        )
                    except Exception as e:
                        self.logger.error(
                            f"[{task.news_id}] Error sending message: {e}"
                        )
                        telegram = Telegram()
                        await telegram.send_message(
                            task.news_id,
                            f"[{task.news_id}] Error sending message: {e}",
                            chat_id=cts.TELEGRAM_CHANNEL_DEBUG,
                        )

            ## ------> UNKNOWN (must never happen) <------ ##
            else:
                self.logger.error(f"Unknown queue: {batch.queue}")
                return
        self.logger.info(f"Finished batch queue {batch.queue} successfully")

    # async def fetch(self, request: Request):
    #     with self.SessionLocal() as session:
    #         if request.url.endswith("/start/testSomething"):
    #             pass

    #         ## ------> UNKNOWN (must never happen) <------ ##
    #         else:
    #             return Response("Not Found", status=404)

    #     ## Success ;)
    #     # self.logger.info("Finished successfully")
    #     # self.logger.error("Finished with errors")
    #     return Response("Success", status=200)
