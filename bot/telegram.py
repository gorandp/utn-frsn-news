import os
import requests
from time import sleep

from .base import Base


DEFAULT_RETRY_SLEEP = 5 # seconds
MAXIMUM_RETRIES = 5

CHAT_ID = '@utnfrsnnews'
TELEGRAM_API_KEY = os.getenv('TELEGRAM_API_KEY')
# NOTE: API Methods
# https://core.telegram.org/bots/api#available-methods
URL_SEND_MESSAGES = f'https://api.telegram.org/bot{TELEGRAM_API_KEY}'\
                    '/sendMessage'
URL_SEND_PHOTO = f'https://api.telegram.org/bot{TELEGRAM_API_KEY}'\
                    '/sendPhoto'


def chunk_message(sequence: list) -> list:
    for i in range(0, len(sequence), 4096):
        yield sequence[i:i + 4096]


class Telegram(Base):
    def __init__(self):
        super().__init__(__name__)

    def send_message(self, _id: str, message: str) -> bool:
        self.logger.info(f"[{_id}] Sending message")
        for _message in chunk_message(message):
            try_counter = 1
            while True:
                body = {
                    'chat_id': CHAT_ID,
                    'text': _message,
                    'parse_mode': 'HTML',
                    # NOTE: Useful when sending a lot of messages
                    # 'disable_notification': True,
                }
                response = requests.post(URL_SEND_MESSAGES, json=body)
                if (
                    response.status_code != 200 and
                    try_counter > MAXIMUM_RETRIES
                ):
                    response = response.json()
                    self.logger.error(f"Couldn't send message after "
                                      f"{try_counter} tries | "
                                      f"{response['error_code']} | "
                                      f"{response['description']}")
                    return False
                if response.status_code == 429:
                    try_counter += 1
                    seconds = response.json()["parameters"]["retry_after"]
                    self.logger.warning("Too many requests. Retry in "
                                        f"{seconds} seconds")
                    sleep(seconds)
                    continue
                if response.status_code != 200:
                    try_counter += 1
                    response = response.json()
                    self.logger.error(f"Couldn't send message (try in "
                                      f"{DEFAULT_RETRY_SLEEP}s) | "
                                      f"{response['error_code']} | "
                                      f"{response['description']}")
                    sleep(DEFAULT_RETRY_SLEEP)
                    continue
                break
        self.logger.info(f"[{_id}] Message sent")
        return True

    def send_photo(self, _id: str, photo_url: str, caption: str) -> bool:
        self.logger.info(f"[{_id}] Sending photo")
        try_counter = 1
        while True:
            if len(caption) > 1024:
                self.logger.warning(f"Long caption: {len(caption)} > 1024. "
                                    "We are cutting it to 1024.")
                caption = caption[:1024]
            body = {
                'chat_id': CHAT_ID,
                'photo': photo_url,
                'caption': caption,
                'parse_mode': 'HTML',
                # NOTE: Useful when sending a lot of messages
                # 'disable_notification': True,
            }
            response = requests.post(URL_SEND_PHOTO, json=body)
            if (
                response.status_code != 200 and
                try_counter > MAXIMUM_RETRIES
            ):
                response = response.json()
                self.logger.error(f"Couldn't send message after "
                                    f"{try_counter} tries | "
                                    f"{response['error_code']} | "
                                    f"{response['description']}")
                return False
            if response.status_code == 429:
                try_counter += 1
                seconds = response.json()["parameters"]["retry_after"]
                self.logger.warning("Too many requests. Retry in "
                                    f"{seconds} seconds")
                sleep(seconds)
                continue
            if response.status_code != 200:
                try_counter += 1
                response = response.json()
                if response['description'] == \
                    "Bad Request: wrong file identifier/HTTP URL specified":
                    self.logger.error("Sending alternative message | "
                                    f"{response['error_code']} | "
                                    f"{response['description']}")
                    message = f'<a href="{photo_url}">FOTO</a> (no se pudo '
                    message += 'cargar la foto)\n\n' + caption
                    return self.send_message(_id, message)
                self.logger.error(f"Couldn't send message with photo (try in "
                                    f"{DEFAULT_RETRY_SLEEP}s) | "
                                    f"{response['error_code']} | "
                                    f"{response['description']}")
                sleep(DEFAULT_RETRY_SLEEP)
                continue
            break
        self.logger.info(f"[{_id}] Photo sent")
        return True
