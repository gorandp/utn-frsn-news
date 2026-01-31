import concurrent.futures
from time import sleep
from typing import Generator

from ..logger import LogWrapper
from .feed import HistoricFeed
from .parser_news import NewsReader


HISTORIC_SLEEP_TIME = 12 * 60 * 60  # 12 hours
SCRAPER_SLEEP_TIME = 6 * 60 * 60  # 6 hours

BATCH_LENGHT = 10


def batch_sequence(sequence: list) -> Generator[list, None, None]:
    for i in range(0, len(sequence), BATCH_LENGHT):
        yield sequence[i : i + BATCH_LENGHT]


class Scraper(LogWrapper):
    def __init__(self):
        super().__init__(__name__)
        self.db = BotDb()  # FIXME: replace with D1
        self.feed = HistoricFeed()
        self.news_reader = NewsReader()

    def process_by_batch(self, urls_batch: list) -> list:
        with concurrent.futures.ThreadPoolExecutor() as executor:  # FIXME: use asyncio
            all_executors = []
            for url_feed in urls_batch:
                all_executors.append(
                    executor.submit(self.news_reader.read_new, *url_feed)
                )
            all_news = []
            for e in all_executors:
                all_news.append(e.result())
        return all_news

    def start(self):
        self.logger.info("Starting bot")

        self.logger.info("Getting historic feed")
        urls = self.feed.get_urls()
        urls.reverse()
        batch = []

        self.logger.info(f"Found {len(urls)} news. Processing in batches.")
        total_batches = len(urls) // BATCH_LENGHT
        if len(urls) % BATCH_LENGHT:
            total_batches += 1

        for batch_idx, batch in enumerate(batch_sequence(urls)):
            self.logger.info(f"Processing batch {batch_idx + 1}/{total_batches}")
            batch = self.db.get_not_existent_urls(batch)
            if not batch:
                self.logger.info("There aren't new news in this batch")
                continue
            all_news = self.process_by_batch(batch)
            self.logger.info(f"Inserting {len(all_news)} news (if don't exist already)")
            all_news = self.db.insert_news_if_not_exist(all_news)
        self.logger.info("Bot end")

    def start_historic(self):
        self.logger.info("Starting historic")
        while True:
            self.logger.info("Getting historic feed")
            urls = self.feed.get_urls()
            urls.reverse()
            urls = self.db.get_not_existent_urls(urls)
            if not urls:
                self.logger.info(
                    f"There aren't new news. Sleeping {HISTORIC_SLEEP_TIME} hs"
                )
                sleep(HISTORIC_SLEEP_TIME)
                continue
            self.db.insert_historic_urls(urls)
