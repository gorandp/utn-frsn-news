from workers import Response, WorkerEntrypoint, Request
from sqlalchemy_cloudflare_d1 import create_engine_from_binding  # type: ignore
from sqlalchemy.orm import sessionmaker, Session
from pyodide.ffi import to_js
from asyncio import sleep
from datetime import datetime, UTC


class Default(WorkerEntrypoint):
    async def fetch(self, request: Request):
        engine = create_engine_from_binding(self.env.DB)  # type: ignore
        SessionLocal = sessionmaker(bind=engine)
        with SessionLocal() as session:
            if request.url.endswith("/start/indexScraper"):
                # TODO: Index Scraper call
                news_urls = []
                # Queue insert
                for url in news_urls:
                    await self.env.SCRAPER_QUEUE.send(
                        to_js(
                            {
                                "url": request.url,
                                "inserted_at": datetime.now(UTC).isoformat(),
                            }
                        )
                    )
                    await sleep(1)  # Throttle
            elif request.url.endswith("/start/mainScraper"):
                # TODO: Main Scraper call
                news_url = ""
                await self.env.MESSENGER_QUEUE.send(
                    to_js(
                        {
                            "news_url": news_url,
                            "inserted_at": datetime.now(UTC).isoformat(),
                        }
                    )
                )
            elif request.url.endswith("/start/messenger"):
                # TODO: Messenger call
                pass
            else:
                return Response("Not Found", status=404)
        return Response("Success", status=200)
