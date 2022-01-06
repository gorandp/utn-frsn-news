from time import time
import os
import requests
import bs4
from datetime import datetime

from .base import Base


TIMEOUT = int(os.getenv('TIMEOUT'))


class NewsReader(Base):
    def __init__(self):
        super().__init__(__name__)

    def read_new(self, url: str, url_photo: str):
        self.logger.debug(f"Getting: {url}")
        response = requests.get(url, timeout=TIMEOUT)
        self.logger.debug(f"Parsing: {url}")
        parse_time = time()
        parser = bs4.BeautifulSoup(
            response.content.decode("utf-8", errors="ignore"),
            "lxml"
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
            new['urlPhoto'] = url_photo
        else:
            del new['urlPhoto']
        self.logger.debug(f"Done parse of: {url}")
        return new
