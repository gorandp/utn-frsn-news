from datetime import datetime, UTC
from workers import WorkerEntrypoint, Request
from pyodide.ffi import to_js
from sqlalchemy_cloudflare_d1 import create_engine_from_binding  # type: ignore
from sqlalchemy.orm import sessionmaker

import app.constants as cts
from app.logger import LogWrapper, LoggerConfig
from app.database_models import Base as DatabaseBaseModel
from app.cloudflare_images import CloudflareConfig
from app.cloudflare_queues import QueueScraper, QueueMessenger

from app.main_apps.messenger.telegram import Telegram
from app.main_apps.main import index_scraper, main_scraper, messenger

from app.fastapi_app.main import app as fastapi_app
from app.fastapi_app.database import db_session


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
            if batch.queue == "utn-frsn-news-scraper":
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
            elif batch.queue == "utn-frsn-news-messenger":
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

    async def fetch(self, request: Request):
        import asgi

        with self.SessionLocal() as session:
            token = db_session.set(session)  # Store session for THIS request only
            try:
                return await asgi.fetch(
                    fastapi_app,
                    request.js_object,
                    self.env,
                )
            finally:
                db_session.reset(token)  # Clean up session after request
