from datetime import datetime, UTC


class QueueScraper:
    @classmethod
    def bulk_new(
        cls,
        urls_tuples: list[tuple[str, str | None]],
        inserted_at: datetime | None = None,
    ):
        return [
            {
                "body": cls.new(
                    news_url,
                    photo_url,
                    inserted_at,
                )
            }
            for news_url, photo_url in urls_tuples
        ]

    @staticmethod
    def new(
        news_url: str,
        photo_url: str | None,
        inserted_at: datetime | None = None,
    ):
        return {
            "news_url": news_url,
            "photo_url": photo_url,
            "inserted_at": inserted_at.isoformat()
            if inserted_at
            else datetime.now(UTC).isoformat(),
        }

    @classmethod
    def read(cls, message):
        return cls(
            news_url=message.body.news_url,
            photo_url=message.body.photo_url,
            inserted_at=message.body.inserted_at,
        )

    def __init__(
        self,
        news_url: str,
        photo_url: str,
        inserted_at: datetime,
    ) -> None:
        self.news_url = news_url
        self.photo_url = photo_url
        self.inserted_at = inserted_at


class QueueMessenger:
    @classmethod
    def bulk_new(
        cls,
        news_ids: list[int],
        inserted_at: datetime | None = None,
    ):
        return [
            {
                "body": cls.new(
                    news_id,
                    inserted_at,
                )
            }
            for news_id in news_ids
        ]

    @staticmethod
    def new(
        news_id: int,
        inserted_at: datetime | None = None,
    ):
        return {
            "news_id": news_id,
            "inserted_at": inserted_at.isoformat()
            if inserted_at
            else datetime.now(UTC).isoformat(),
        }

    @classmethod
    def read(cls, message):
        return cls(
            news_id=message.body.news_id,
            inserted_at=message.body.inserted_at,
        )

    def __init__(
        self,
        news_id: int,
        inserted_at: datetime,
    ) -> None:
        self.news_id = news_id
        self.inserted_at = inserted_at
