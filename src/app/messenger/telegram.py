import asyncio
from pyodide.http import pyfetch
from typing import Generator
import json

from ..logger import LogWrapper
from ..constants import TELEGRAM_CHANNEL_DEBUG


def chunk_message(sequence: str) -> Generator[str, None, None]:
    for i in range(0, len(sequence), 4096):
        yield sequence[i : i + 4096]


class Telegram(LogWrapper):
    CHAT_ID: str = TELEGRAM_CHANNEL_DEBUG
    TELEGRAM_API_KEY: str = ""
    URL_SEND_MESSAGES: str = ""
    URL_SEND_PHOTO: str = ""
    DEFAULT_RETRY_SLEEP: int = 5  # seconds
    MAXIMUM_RETRIES: int = 5
    SILENT_MODE: bool = False

    @classmethod
    def setup_config(
        cls,
        chat_id: str = "",
        telegram_api_key: str = "",
        silent_mode: bool = False,
    ) -> None:
        if chat_id:
            cls.CHAT_ID = chat_id
        if telegram_api_key:
            cls.TELEGRAM_API_KEY = telegram_api_key
            # NOTE: API Methods
            # https://core.telegram.org/bots/api#available-methods
            cls.URL_SEND_MESSAGES = (
                f"https://api.telegram.org/bot{telegram_api_key}/sendMessage"
            )
            cls.URL_SEND_PHOTO = (
                f"https://api.telegram.org/bot{telegram_api_key}/sendPhoto"
            )
        if silent_mode:
            cls.SILENT_MODE = silent_mode

    async def send_message(
        self,
        news_id: int,
        message: str,
        chat_id: str | None = None,
    ) -> bool:
        if self.TELEGRAM_API_KEY == "":
            self.logger.error("Telegram API Key is not set up")
            return False
        if chat_id is None:
            chat_id = self.CHAT_ID
        self.logger.info(f"[{news_id}] Sending message")
        for _message in chunk_message(message):
            try_counter = 1
            while True:
                body = {
                    "chat_id": chat_id,
                    "text": _message,
                    "parse_mode": "HTML",
                    # NOTE: Useful when sending a lot of messages
                    "disable_notification": self.SILENT_MODE,
                }
                response = await pyfetch(
                    self.URL_SEND_MESSAGES,
                    method="POST",
                    headers={
                        "Content-Type": "application/json",
                    },
                    body=json.dumps(body),
                )
                if response.status != 200 and try_counter > self.MAXIMUM_RETRIES:
                    response = await response.json()
                    self.logger.error(
                        f"Couldn't send message after "
                        f"{try_counter} tries | "
                        f"{response['error_code']} | "
                        f"{response['description']}"
                    )
                    return False
                if response.status == 429:
                    try_counter += 1
                    seconds = (await response.json())["parameters"]["retry_after"]
                    self.logger.warning(
                        f"Too many requests. Retry in {seconds} seconds"
                    )
                    await asyncio.sleep(seconds)
                    continue
                if response.status != 200:
                    try_counter += 1
                    response = await response.json()
                    self.logger.error(
                        f"Couldn't send message (try in "
                        f"{self.DEFAULT_RETRY_SLEEP}s) | "
                        f"{response['error_code']} | "
                        f"{response['description']}"
                    )
                    await asyncio.sleep(self.DEFAULT_RETRY_SLEEP)
                    continue
                break
        self.logger.info(f"[{news_id}] Message sent")
        return True

    async def send_photo(
        self,
        news_id: int,
        photo_url: str,
        caption: str,
        chat_id: str | None = None,
    ) -> bool:
        if self.TELEGRAM_API_KEY == "":
            self.logger.error("Telegram API Key is not set up")
            return False
        if chat_id is None:
            chat_id = self.CHAT_ID
        self.logger.info(f"[{news_id}] Sending photo")
        try_counter = 1
        while True:
            if len(caption) > 1024:
                self.logger.warning(
                    f"Long caption: {len(caption)} > 1024. We are cutting it to 1024."
                )
                caption = caption[:1024]
            body = {
                "chat_id": chat_id,
                "photo": photo_url,
                "caption": caption,
                "parse_mode": "HTML",
                # NOTE: Useful when sending a lot of messages
                "disable_notification": self.SILENT_MODE,
            }
            response = await pyfetch(
                self.URL_SEND_PHOTO,
                method="POST",
                headers={
                    "Content-Type": "application/json",
                },
                body=json.dumps(body),
            )
            if response.status != 200 and try_counter > self.MAXIMUM_RETRIES:
                response = await response.json()
                self.logger.error(
                    f"Couldn't send message after "
                    f"{try_counter} tries | "
                    f"{response['error_code']} | "
                    f"{response['description']}"
                )
                return False
            if response.status == 429:
                try_counter += 1
                seconds = (await response.json())["parameters"]["retry_after"]
                self.logger.warning(f"Too many requests. Retry in {seconds} seconds")
                await asyncio.sleep(seconds)
                continue
            if response.status != 200:
                try_counter += 1
                response = await response.json()
                if (
                    response["description"]
                    == "Bad Request: wrong file identifier/HTTP URL specified"
                ):
                    self.logger.error(
                        "Sending alternative message | "
                        f"{response['error_code']} | "
                        f"{response['description']}"
                    )
                    message = f'<a href="{photo_url}">FOTO</a> (no se pudo '
                    message += "cargar la foto)\n\n" + caption
                    return await self.send_message(news_id, message)
                self.logger.error(
                    f"Couldn't send message with photo (try in "
                    f"{self.DEFAULT_RETRY_SLEEP}s) | "
                    f"{response['error_code']} | "
                    f"{response['description']}"
                )
                await asyncio.sleep(self.DEFAULT_RETRY_SLEEP)
                continue
            break
        self.logger.info(f"[{news_id}] Photo sent")
        return True
