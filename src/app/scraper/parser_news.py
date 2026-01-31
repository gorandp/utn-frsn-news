import os
import bs4
from pyodide.http import pyfetch
from datetime import datetime, UTC
from time import time

from ..logger import LogWrapper


TIMEOUT = int(os.getenv("TIMEOUT") or "60")


class NewsReader(LogWrapper):
    async def read_new(
        self,
        url: str,
        url_photo: str,
    ):
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
            "publishedDatetime": datetime.fromisoformat(
                str(entry_date.attrs["datetime"])
            )
            if entry_date
            else None,
            "insertedDatetime": datetime.now(UTC),
            "url": url,
            "title": title,
            "body": body,
            "urlPhoto": url_photo,
            "responseElapsedTime": fetch_time,
            "parseElapsedTime": time() - parse_time,
        }
        if not url_photo:
            del new["urlPhoto"]
        # self.logger.debug(f"Done parse of: {url}")
        return new
