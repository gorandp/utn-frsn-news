import asyncio
import os
import bs4
from pyodide.http import pyfetch

from ...logger import LogWrapper


class WORDPRESS_SITE:
    TIMEOUT = int(os.getenv("TIMEOUT") or "60")
    HISTORIC_FEED_URL = "https://www.frsn.utn.edu.ar/?paged=1&page_id=80"
    REGEX_HISTORIC_FEED = r"/\?p=\d+"
    PAGINATION_URL = "https://www.frsn.utn.edu.ar/?paged={}&page_id=80"


class HistoricFeed(LogWrapper):
    async def get_data(self, soup: bs4.BeautifulSoup) -> list[tuple[str, str | None]]:
        """Parse news list page

        :param soup: News list page
        :type soup: bs4.BeautifulSoup
        :return: List of tuples with news URL and photo URL
        :rtype: list[tuple[str, str | None]]
        """
        urls: list[tuple[str, str | None]] = []
        for index, new in enumerate(soup.select("article.post")):
            new_url = new.find("a")
            if not new_url:
                self.logger.error(f"No URL found for news item {index}.")
                continue
            new_url = new_url.attrs["href"]
            photo_url = new.find("img")
            if photo_url:
                photo_url = photo_url.attrs["src"]
            urls.append(
                (
                    str(new_url),
                    str(photo_url) if photo_url else None,
                )
            )
        return urls

    async def fetch_and_get_data(
        self,
        page: int,
    ):
        response = await pyfetch(
            WORDPRESS_SITE.PAGINATION_URL.format(page),
        )
        # TODO: abort fetch after WORDPRESS_SITE.TIMEOUT is reached
        content = await response.bytes()
        soup = bs4.BeautifulSoup(
            content.decode("utf-8", errors="ignore"),
            "html.parser",
        )
        return await self.get_data(soup)

    async def get_urls(
        self,
        latest_url: str | None = None,
    ) -> list[tuple[str, str | None]]:
        """Get all news URLs from the historic feed

        :param latest_url: Latest URL to stop at, defaults to None
        :type latest_url: str | None, optional
        :return: List of tuples with news URL and photo URL
        :rtype: list[tuple[str, str | None]]
        """
        self.logger.info("Starting to fetch historic feed URLs.")
        urls: list[tuple[str, str | None]] = []

        # TODO: abort fetch after WORDPRESS_SITE.TIMEOUT is reached
        response = await pyfetch(WORDPRESS_SITE.HISTORIC_FEED_URL)
        content = await response.bytes()
        soup = bs4.BeautifulSoup(
            content.decode("utf-8", errors="ignore"),
            "html.parser",
        )
        last_page = int(soup.select("nav > div > a.page-numbers")[-2].text)
        urls.extend(await self.get_data(soup))
        if latest_url and latest_url in [u[0] for u in urls[:-5]]:
            # If we found the latest_url in the first page, return early
            return urls
        page = 2
        tasks = []
        while page <= last_page:
            tasks.append(asyncio.create_task(self.fetch_and_get_data(page)))
            await asyncio.sleep(0.5)  # Throttle
            page += 1
            if page % 5 == 0:
                # Process tasks in batches of 5 pages
                for task in tasks:
                    # Await each task to get the URLs for that page
                    urls.extend(await task)
                tasks = []
                if latest_url and latest_url in [u[0] for u in urls[:-5]]:
                    # If we found the latest_url, stop processing further pages
                    return urls
        # Process any remaining tasks
        for task in tasks:
            urls.extend(await task)

        return reversed(urls)
