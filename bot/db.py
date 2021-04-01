import os
from datetime import datetime
import re

from .mongo import DB
from .base import Base

regex_url = re.compile(r"https://www.frsn.utn.edu.ar/frsn/selec_seccion.asp\?"
                       r"IDSeccion=(\d+)&IDSub=(\d+)&ContentID=(\d+)")

def get_order(url: str):
    m = regex_url.match(url)
    if m:
        return int(m.group(1)), int(m.group(2)), int(m.group(3))
    raise ValueError("Match error")


class BotDb(Base):
    def __init__(self):
        super().__init__(__name__)
        self.db = DB(
            DATABASE_NAME="news_db",
            DB_CONNECTION_STRING=os.getenv('DB_CONNECTION_STRING')
        )

    def insert_historic_urls(self, news_urls: list) -> list:
        query = {'url': {'$in': [u[0] for u in news_urls]}}
        result = self.db.database["news"].find(query, projection={'url': 1})
        for r in result:
            for url in news_urls:
                if url[0] == r['url']:
                    news_urls.remove(url)
                    break
        docs = [
            {
                "insertedDate": datetime.utcnow(),
                "status": 0,
                "url": n[0],
                "urlPhoto": n[1],
                "idSeccion": get_order(n[0])[0],
                "idSub": get_order(n[0])[1],
                "contentId": get_order(n[0])[2]
            }
            for n in news_urls
        ]
        self.db.database["historic"].insert_many(docs)
        self.logger.info(f"Inserted {len(docs)} historic data")

    def get_not_existent_urls(self, news_urls: list) -> list:
        query = {'url': {'$in': [u[0] for u in news_urls]}}
        result = self.db.database["news"].find(query, projection={'url': 1})
        for r in result:
            for url in news_urls:
                if url[0] == r['url']:
                    news_urls.remove(url)
                    break
        return news_urls

    def insert_news_if_not_exist(self, news: list) -> list:
        """Insert non existing news and return only which aren't on DB

        :param news: News
        :type news: list
        :return: News inserted
        :rtype: list
        """
        news_urls = [new['url'] for new in news]
        query = {'url': {'$in': news_urls}}
        result = self.db.database["news"].find(query, projection={'url': 1})
        for r in result:
            news_urls.remove(r['url'])
        if news_urls:
            news = [_new for _new in news if _new['url'] in news_urls]
            result = self.db.database["news"].insert_many(news)
        else:
            news = []
        self.logger.info(f"{len(news)} news inserted")
        self.insert_messager_queue(news)
        return news

    def insert_messager_queue(self, news: list) -> list:
        messager_queue = [
            {
                'url': n['url'],
                'insertedDate': datetime.utcnow(),
                'lastUpdateDate': datetime.utcnow(),
                'status': 0,
            }
            for n in news
        ]
        if messager_queue:
            self.db.database["messagerQueue"].insert_many(messager_queue)
        self.logger.info(f"{len(messager_queue)} elements inserted in "
                         "messager queue")

    def get_unprocessed_messager_queue(self) -> list:
        result = self.db.database["messagerQueue"].find({
            'status': 0
        })
        result = sorted([r for r in result], key=lambda doc: get_order(doc['url']))
        return result

    def get_news(self, messagerQueue: list) -> list:
        urlQueue = [q['url'] for q in messagerQueue]
        result = self.db.database["news"].find({
            'url': {'$in': urlQueue}
        })
        result = sorted([r for r in result], key=lambda doc: get_order(doc['url']))
        return result

    def set_as_processed_in_messager_queue(self, new_url: str) -> None:
        self.db.database["messagerQueue"].update_one(
            {"url": new_url}, {"$set": {"status": 1}}
        )

    def set_as_error_in_messager_queue(self, new_url: str) -> None:
        self.db.database["messagerQueue"].update_one(
            {"url": new_url}, {"$set": {"status": -1}}
        )
