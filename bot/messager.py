from time import sleep
import re

from .message_formatter import (build_message, build_message_header)
from .db import BotDb
from .base import Base
from .telegram import Telegram


SLEEP_TIME = 12*60*60 # 12 hours

old_site_regex_url = re.compile(
    r"https://wwwsi.frsn.utn.edu.ar/frsn/selec_seccion.asp\?"
    r"IDSeccion=(\d+)&IDSub=(\d+)&ContentID=(\d+)")
wordpress_regex_url = re.compile(
    r"https://www.frsn.utn.edu.ar/\?p=(\d+)"
)

def gen_id_from_url(url: str):
    m = wordpress_regex_url.match(url)
    if m:
        return f"wordpress2023-{m.group(1)}"
    m = old_site_regex_url.match(url)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    raise ValueError("Match error")


class Messager(Base):
    def __init__(self):
        super().__init__(__name__)
        self.db = BotDb()

    def process_queue(self):
        # while True:
        self.logger.info("Check queue")
        queue = self.db.get_unprocessed_messager_queue()
        if not queue:
            self.logger.info("There aren't news to send")
            return
            # self.logger.info("There aren't news to send (sleeping "
            #                 f"{SLEEP_TIME / 3600:.2f} hours)")
            # sleep(SLEEP_TIME)
            # continue
        all_news = self.db.get_news(queue)
        del queue

        self.logger.info(f"Sending {len(all_news)} news to telegram")
        telegram = Telegram()
        for _new in all_news:
            _id = gen_id_from_url(_new['url'])
            message = build_message(_new)
            message_header = build_message_header(_new)
            if 'urlPhoto' in _new:
                r = telegram.send_photo(
                    _id,
                    _new['urlPhoto'],
                    message_header
                )
                if r is False:
                    self.db.set_as_error_in_messager_queue(_new['url'])
                    continue
            r = telegram.send_message(
                _id,
                message
            )
            if r is False:
                self.db.set_as_error_in_messager_queue(_new['url'])
                continue
            self.db.set_as_processed_in_messager_queue(_new['url'])
