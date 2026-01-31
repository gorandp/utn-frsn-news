from workers import Response, WorkerEntrypoint, Request
from sqlalchemy_cloudflare_d1 import create_engine_from_binding  # type: ignore
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import select
from pyodide.ffi import to_js
from datetime import datetime, UTC
import json

from app.database_models import News, Base as DatabaseBaseModel
from app.scraper.feed import HistoricFeed
from app.logger import LogWrapper, LoggerConfig


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


class EntryLogger(LogWrapper):
    pass


class Default(WorkerEntrypoint):
    def __init__(self, ctx, env):
        super().__init__(ctx, env)
        LoggerConfig.set_level(self.env.LOGGER_LEVEL)
        self.logger = EntryLogger().logger
        engine = create_engine_from_binding(self.env.DB)  # type: ignore
        self.SessionLocal = sessionmaker(bind=engine)
        DatabaseBaseModel.metadata.create_all(bind=engine)

    async def fetch(self, request: Request):
        with self.SessionLocal() as session:
            ## ------> Index Scraper <------ ##
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
                # TODO: Main Scraper call
                news_id = 1000  # FIXME: Placeholder
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
        self.logger.info(f"Batch queue {batch.queue}")
        ## ------> SCRAPER_QUEUE <------ ##
        if batch.queue == "653f3c467afd43278463cb87292d1c97":
            self.logger.info("Processing SCRAPER_QUEUE batch")
        ## ------> MESSENGER_QUEUE <------ ##
        elif batch.queue == "a0f45ea683634af2a991a1dd7379f9eb":
            self.logger.info("Processing MESSENGER_QUEUE batch")
        ## ------> UNKNOWN (must never happen) <------ ##
        else:
            self.logger.error(f"Unknown queue: {batch.queue}")
            return
        for message in batch.messages:
            self.logger.info(f"Received {message}")
            # self.logger.info(f"Received dir {dir(message)}")
            # self.logger.info(f"Received body {message.body}")
            # self.logger.info(f"Received body dir {dir(message.body)}")
            # self.logger.info(f"Received body news_id {message.body.news_id}")
            # self.logger.info(f"Received body inserted_at {message.body.inserted_at}")

    async def scheduled(self, controller, env, ctx):
        with self.SessionLocal() as session:
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
