from workers import Response, WorkerEntrypoint, Request
from sqlalchemy_cloudflare_d1 import create_engine_from_binding  # type: ignore
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import select
from pyodide.ffi import to_js
from datetime import datetime, UTC
import json

from app.database_models import News, Base as DatabaseBaseModel
from app.scraper.feed import HistoricFeed
from app.scraper.news import NewsReader
from app.cloudflare_images import CloudflareImages, CloudflareConfig
from app.logger import LogWrapper, LoggerConfig


# from contextvars import ContextVar
# # ContextVar to handle session context safely
# db_session: ContextVar[Session] = ContextVar("db_session")


class QueueScraper:
    @classmethod
    def bulk_new(
        cls,
        urls_tuples: list[tuple[str, str | None]],
        inserted_at: datetime | None = None,
    ):
        return [
            cls.new(news_url, photo_url, inserted_at)
            for news_url, photo_url in urls_tuples
        ]

    @staticmethod
    def new(
        news_url: str,
        photo_url: str | None,
        inserted_at: datetime | None = None,
    ):
        return {
            "news_url": news_url,
            "photo_url": photo_url,
            "inserted_at": inserted_at.isoformat()
            if inserted_at
            else datetime.now(UTC).isoformat(),
        }

    @classmethod
    def read(cls, message):
        return cls(
            news_url=message.body.news_url,
            photo_url=message.body.photo_url,
            inserted_at=message.body.inserted_at,
        )

    def __init__(
        self,
        news_url: str,
        photo_url: str,
        inserted_at: datetime,
    ) -> None:
        self.news_url = news_url
        self.photo_url = photo_url
        self.inserted_at = inserted_at


class QueueMessenger:
    @classmethod
    def bulk_new(
        cls,
        news_ids: list[int],
        inserted_at: datetime | None = None,
    ):
        return [cls.new(news_id, inserted_at) for news_id in news_ids]

    @staticmethod
    def new(
        news_id: int,
        inserted_at: datetime | None = None,
    ):
        return {
            "news_id": news_id,
            "inserted_at": inserted_at.isoformat()
            if inserted_at
            else datetime.now(UTC).isoformat(),
        }

    @classmethod
    def read(cls, message):
        return cls(
            news_id=message.body.news_id,
            inserted_at=message.body.inserted_at,
        )

    def __init__(
        self,
        news_id: int,
        inserted_at: datetime,
    ) -> None:
        self.news_id = news_id
        self.inserted_at = inserted_at


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


class EntryLogger(LogWrapper):
    pass


class Default(WorkerEntrypoint):
    def __init__(self, ctx, env):
        super().__init__(ctx, env)
        LoggerConfig.set_level(self.env.LOGGER_LEVEL)
        self.logger = EntryLogger().logger
        engine = create_engine_from_binding(self.env.DB)
        self.SessionLocal = sessionmaker(bind=engine)
        DatabaseBaseModel.metadata.create_all(bind=engine)
        CloudflareConfig.setup(
            account_id=self.env.CLOUDFLARE_ACCOUNT_ID,
            images_account_hash=self.env.CLOUDFLARE_IMAGES_ACCOUNT_HASH,
            images_api_token=self.env.CLOUDFLARE_IMAGES_API_TOKEN,
        )

    async def fetch(self, request: Request):
        with self.SessionLocal() as session:
            ## ------> Index Scraper <------ ##
            ## ____ WORKING - VALIDATED ____ ##
            if request.url.endswith("/start/indexScraper"):
                news_urls = await index_scraper(session)
                return Response(
                    body=json.dumps({"news_urls": news_urls}),
                    headers={"Content-Type": "application/json"},
                    status=200,
                )

            elif request.url.endswith("/start/indexScraperPlusQueue"):
                news_urls = await index_scraper(session)
                if news_urls:
                    await self.env.SCRAPER_QUEUE.sendBatch(
                        to_js(
                            [
                                {
                                    "news_url": url_tuple[0],
                                    "photo_url": url_tuple[1],
                                    "inserted_at": datetime.now(UTC).isoformat(),
                                }
                                for url_tuple in news_urls
                            ]
                        )
                    )

            ## ------> Main Scraper <------ ##
            elif request.url.endswith("/start/mainScraper"):
                news_url = "https://www.frsn.utn.edu.ar/?p=6569"
                photo_url = "https://www.frsn.utn.edu.ar/wp-content/uploads/2025/12/posgrado-2026-slide.jpg"
                # TODO: Main Scraper call
                news_id = await main_scraper(
                    session,
                    news_url,
                    photo_url,
                    datetime.now(UTC),
                )
                await self.env.MESSENGER_QUEUE.send(
                    to_js(
                        {
                            "url": "/start/messenger",
                            "news_id": news_id,
                            "inserted_at": datetime.now(UTC).isoformat(),
                        }
                    )
                )
                await self.env.SCRAPER_QUEUE.send(
                    to_js(
                        {
                            "news_url": "https//example.com/news/1",
                            "photo_url": "https//example.com/photos/1",
                            "inserted_at": datetime.now(UTC).isoformat(),
                        }
                    )
                )

            ## ------> Messenger <------ ##
            elif request.url.endswith("/start/messenger"):
                # TODO: Messenger call
                pass

            ## ------> UNKNOWN (must never happen) <------ ##
            else:
                return Response("Not Found", status=404)

        ## Success ;)
        # self.logger.info("Finished successfully")
        # self.logger.error("Finished with errors")
        return Response("Success", status=200)

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
                    news_id = await main_scraper(
                        session,
                        task.news_url,
                        task.photo_url,
                        datetime.now(UTC),
                    )
                    await self.env.MESSENGER_QUEUE.send(
                        to_js(QueueMessenger.new(news_id))
                    )

            ## ------> MESSENGER_QUEUE <------ ##
            elif batch.queue == "a0f45ea683634af2a991a1dd7379f9eb":
                self.logger.info("Processing MESSENGER_QUEUE batch")
                for message in batch.messages:
                    task = QueueMessenger.read(message)
                    self.logger.info(f"News ID to process: {task.news_id}")

            ## ------> UNKNOWN (must never happen) <------ ##
            else:
                self.logger.error(f"Unknown queue: {batch.queue}")
                return

    async def scheduled(self, controller, env, ctx):
        with self.SessionLocal() as session:
            news_urls = await index_scraper(session)
            if news_urls:
                await self.env.SCRAPER_QUEUE.sendBatch(
                    to_js(QueueScraper.bulk_new(news_urls))
                )
