import os
import requests
import bs4
import re

from .base import Base


class OLD_SITE:
    TIMEOUT = int(os.getenv('TIMEOUT'))
    HISTORIC_FEED_URL = "https://wwwsi.frsn.utn.edu.ar/frsn/selec_seccion.asp?"\
                        "IDSeccion=196&IDSub=197&ContentID=300"
    SHORT_FEED_URL = "https://wwwsi.frsn.utn.edu.ar/frsn/index_posta.asp"
    REGEX_HISTORIC_FEED = (r"selec_seccion\.asp\?IDSeccion=\d+&IDSub=\d+&"
                           r"ContentID=\d+")


class WORDPRESS_SITE:
    TIMEOUT = int(os.getenv('TIMEOUT'))
    HISTORIC_FEED_URL = "https://www.frsn.utn.edu.ar/?paged=1&page_id=80"
    REGEX_HISTORIC_FEED = r"/\?p=\d+"
    PAGINATION_URL = "https://www.frsn.utn.edu.ar/?paged={}&page_id=80"


class HistoricFeed(Base):
    def __init__(self):
        super().__init__(__name__)

    def get_urls(self, limit: int = None):
        response = requests.get(
            WORDPRESS_SITE.HISTORIC_FEED_URL, timeout=WORDPRESS_SITE.TIMEOUT)
        soup = bs4.BeautifulSoup(
            response.content.decode("utf-8", errors="ignore"),
            "lxml"
        )
        urls = []
        last_page = int(soup.select("nav > div > a.page-numbers")[-2].text)
        for page in range(1, last_page+1):
            if page > 1:
                response = requests.get(
                    WORDPRESS_SITE.PAGINATION_URL.format(page),
                    timeout=WORDPRESS_SITE.TIMEOUT)
                soup = bs4.BeautifulSoup(
                    response.content.decode("utf-8", errors="ignore"),
                    "lxml"
                )
            for index, new in enumerate(soup.select("article.post")):
                if limit is not None and index >= limit:
                    break
                new_url = new.find("a").attrs["href"]
                photo_url = new.find("img")
                if photo_url:
                    photo_url = photo_url.attrs["src"]
                urls.append((new_url, photo_url))
        return urls

    def get_urls_old_site(self, limit: int = None):
        response = requests.get(
            OLD_SITE.HISTORIC_FEED_URL, timeout=OLD_SITE.TIMEOUT)
        parser = bs4.BeautifulSoup(
            response.content.decode("utf-8", errors="ignore"),
            "lxml"
        )
        urls = []
        for index, new in enumerate(parser.find_all(
            "a", attrs={'href': re.compile(OLD_SITE.REGEX_HISTORIC_FEED)}
        )):
            if limit is not None and index >= limit:
                break
            href = new.attrs["href"]
            new_url = "https://wwwsi.frsn.utn.edu.ar/frsn/" + href

            table_new = new.findParents('table')[0]
            photo_url = table_new.find("img")
            if photo_url:
                photo_url = (
                    "https://wwwsi.frsn.utn.edu.ar"
                    + photo_url.attrs["src"]
                )

            urls.append((new_url, photo_url))
        return urls


class ShortFeed(Base):
    def __init__(self):
        super().__init__(__name__)

    def get_urls(self):
        response = requests.get(
            OLD_SITE.SHORT_FEED_URL, timeout=OLD_SITE.TIMEOUT)
        parser = bs4.BeautifulSoup(
            response.content.decode("utf-8", errors="ignore"),
            "lxml"
        )
        urls = []
        for new in parser.find_all("a", attrs={"class": "titulohome"}):
            href = new.attrs["href"]
            new_url = "https://wwwsi.frsn.utn.edu.ar/frsn/" + href
            urls.append(new_url)
        return urls
