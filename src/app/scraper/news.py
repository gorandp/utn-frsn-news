import os
import bs4
from pyodide.http import pyfetch
from datetime import datetime
from time import time

from ..logger import LogWrapper


TIMEOUT = int(os.getenv("TIMEOUT") or "60")


class NewsReader(LogWrapper):
    async def read_news(self, url: str):
        # self.logger.debug(f"Getting: {url}")
        fetch_time = time()
        # TODO: abort fetch after TIMEOUT is reached
        response = await pyfetch(url)
        content = await response.bytes()
        fetch_time = time() - fetch_time
        # self.logger.debug(f"Parsing: {url}")
        parse_time = time()
        soup = bs4.BeautifulSoup(
            content.decode("utf-8", errors="ignore"),
            "html.parser",
        )
        title = soup.find("h1")
        body = soup.select_one("div.entry-content")
        entry_date = soup.select_one("time.entry-date")
        title = title.text.strip() if title else ""
        body = body.text.replace("\n", "\n\n").strip() if body else ""
        new = {
            "origin_created_at": datetime.fromisoformat(
                str(entry_date.attrs["datetime"])
            )
            if entry_date
            else None,
            "url": url,
            "title": title,
            "content": body,
            "response_elapsed_seconds": fetch_time,
            "parse_elapsed_seconds": time() - parse_time,
        }
        # self.logger.debug(f"Done parse of: {url}")
        return new

    async def fetch_image(self, url: str | None) -> bytes | None:
        if not url:
            return None
        # self.logger.debug(f"Fetching image: {url}")
        response = await pyfetch(url)
        content = await response.bytes()
        # self.logger.debug(f"Done fetch of image: {url}")
        return content
