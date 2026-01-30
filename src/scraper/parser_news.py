from time import time
import os
import requests
import bs4
from datetime import datetime

from ..logger import LogWrapper


TIMEOUT = int(os.getenv("TIMEOUT") or "60")


class NewsReader(LogWrapper):
    def __init__(self):
        super().__init__(__name__)

    def read_new(self, url: str, url_photo: str):
        self.logger.debug(f"Getting: {url}")
        response = requests.get(url, timeout=TIMEOUT)
        self.logger.debug(f"Parsing: {url}")
        parse_time = time()
        soup = bs4.BeautifulSoup(
            response.content.decode("utf-8", errors="ignore"), "lxml"
        )
        title = soup.find("h1")
        body = soup.select_one("div.entry-content")
        entry_date = soup.select_one("time.entry-date")
        title = title.text.strip() if title else ""
        body = body.text.replace("\n", "\n\n").strip() if body else ""
        new = {
            "publishedDatetime": datetime.fromisoformat(entry_date.attrs["datetime"])
            if entry_date
            else None,
            "insertedDatetime": datetime.utcnow(),
            "url": url,
            "title": title,
            "body": body,
            "urlPhoto": url_photo,
            "responseElapsedTime": response.elapsed.total_seconds(),
            "parseElapsedTime": time() - parse_time,
        }
        if not url_photo:
            del new["urlPhoto"]
        self.logger.debug(f"Done parse of: {url}")
        return new

    def read_new_old_site(self, url: str, url_photo: str):
        self.logger.debug(f"Getting: {url}")
        response = requests.get(url, timeout=TIMEOUT)
        self.logger.debug(f"Parsing: {url}")
        parse_time = time()
        parser = bs4.BeautifulSoup(
            response.content.decode("utf-8", errors="ignore"), "lxml"
        )
        title = parser.find("td", attrs={"class": "textotitulo"})
        body = parser.find("table", attrs={"class": "textohome"})
        title = title.text.strip() if title else ""
        body = body.text.strip() if body else ""
        new = {
            "insertedDatetime": datetime.utcnow(),
            "url": url,
            "title": title,
            "body": body,
            "urlPhoto": url_photo,
            "responseElapsedTime": response.elapsed.total_seconds(),
            "parseElapsedTime": time() - parse_time,
        }
        if url_photo:
            new["urlPhoto"] = url_photo
        else:
            del new["urlPhoto"]
        self.logger.debug(f"Done parse of: {url}")
        return new
