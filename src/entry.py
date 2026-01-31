from workers import Response, WorkerEntrypoint, Request
from sqlalchemy_cloudflare_d1 import create_engine_from_binding  # type: ignore
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import select
from pyodide.ffi import to_js
from asyncio import sleep
from datetime import datetime, UTC

from app.database_models import News
from app.scraper.feed import HistoricFeed
from app.logger import LogWrapper


async def index_scraper(session: Session):
    # Get latest URL from DB
    latest_url = session.execute(
        select(News.url).order_by(News.origin_created_at.desc()).limit(1)
    ).scalar_one_or_none()

    # Get news URLs from historic feed
    historic_feed = HistoricFeed()
    news_urls = await historic_feed.get_urls(latest_url=latest_url)

    # Check existing URLs in DB
    existing_urls = (
        session.execute(select(News.url).where(News.url.in_([u[0] for u in news_urls])))
        .scalars()
        .all()
    )

    # Filter out existing URLs
    return [u for u in news_urls if u[0] not in existing_urls]


class Default(WorkerEntrypoint):
    async def fetch(self, request: Request):
        log = LogWrapper()
        engine = create_engine_from_binding(self.env.DB)  # type: ignore
        SessionLocal = sessionmaker(bind=engine)
        with SessionLocal() as session:
            ## ------> Index Scraper <------ ##
            if request.url.endswith("/start/indexScraper"):
                news_urls = await index_scraper(session)
                for url_tuple in news_urls:
                    # Queue insert
                    await self.env.SCRAPER_QUEUE.send(
                        to_js(
                            {
                                "news_url": url_tuple[0],
                                "photo_url": url_tuple[1],
                                "inserted_at": datetime.now(UTC).isoformat(),
                            }
                        )
                    )
                    await sleep(1)  # Throttle

            ## ------> Main Scraper <------ ##
            elif request.url.endswith("/start/mainScraper"):
                # TODO: Main Scraper call
                news_id = 12345  # FIXME: Placeholder
                await self.env.MESSENGER_QUEUE.send(
                    to_js(
                        {
                            "url": "/start/messenger",
                            "news_id": news_id,
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
        log.logger.info("Finished successfully")
        return Response("Success", status=200)

    async def queue(self, batch, a, b):
        log = LogWrapper()
        for message in batch.messages:
            print("Received", message)
