import os
import requests
import bs4
import re

from .base import Base


TIMEOUT = int(os.getenv('TIMEOUT'))

HISTORIC_FEED_URL = "https://www.frsn.utn.edu.ar/frsn/selec_seccion.asp?"\
                    "IDSeccion=196&IDSub=197&ContentID=300"
SHORT_FEED_URL = "https://www.frsn.utn.edu.ar/frsn/index_posta.asp"

REGEX_HISTORIC_FEED = (r"selec_seccion\.asp\?IDSeccion=\d+&IDSub=\d+&"
                       r"ContentID=\d+")


class HistoricFeed(Base):
    def __init__(self):
        super().__init__(__name__)

    def get_urls(self, limit: int = None):
        response = requests.get(HISTORIC_FEED_URL, timeout=TIMEOUT)
        parser = bs4.BeautifulSoup(
            response.content.decode("utf-8", errors="ignore"),
            "lxml"
        )
        urls = []
        for index, new in enumerate(parser.find_all(
            "a", attrs={'href': re.compile(REGEX_HISTORIC_FEED)}
        )):
            if limit is not None and index >= limit:
                break
            href = new.attrs["href"]
            new_url = "https://www.frsn.utn.edu.ar/frsn/" + href

            table_new = new.findParents('table')[0]
            photo_url = table_new.find("img")
            if photo_url:
                photo_url = (
                    "https://www.frsn.utn.edu.ar"
                    + photo_url.attrs["src"]
                )

            urls.append((new_url, photo_url))
        return urls


class ShortFeed(Base):
    def __init__(self):
        super().__init__(__name__)

    def get_urls(self):
        response = requests.get(SHORT_FEED_URL, timeout=TIMEOUT)
        parser = bs4.BeautifulSoup(
            response.content.decode("utf-8", errors="ignore"),
            "lxml"
        )
        urls = []
        for new in parser.find_all("a", attrs={"class": "titulohome"}):
            href = new.attrs["href"]
            new_url = "https://www.frsn.utn.edu.ar/frsn/" + href
            urls.append(new_url)
        return urls
