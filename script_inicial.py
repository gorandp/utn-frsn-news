from datetime import datetime, timezone
from time import time
import concurrent.futures
import requests
import bs4


URL_FEED = "https://www.frsn.utn.edu.ar/frsn/index_posta.asp"
TIMEOUT = 60*3 # seconds = 3 minutes


class NewFeed():
    def get_urls(self):
        content = requests.get(URL_FEED, timeout=TIMEOUT)
        parser = bs4.BeautifulSoup(content.text, "lxml")
        urls = []
        for new in parser.find_all("a", attrs={"class": "titulohome"}):
            href = new.attrs["href"]
            new_url = "https://www.frsn.utn.edu.ar/frsn/" + href
            urls.append(new_url)
        return urls

class NewReader():
    def read_new(self, url):
        content = requests.get(url, timeout=TIMEOUT)
        parse_time = time()
        parser = bs4.BeautifulSoup(content.text, "lxml")
        title = parser.find("td", attrs={"class": "textotitulo"})
        body = parser.find("table", attrs={"class": "textohome"})
        title = title.text.strip() if title else ""
        body = body.text.strip() if body else ""
        new = {
            "insertedDatetime": datetime.utcnow().replace(
                tzinfo=timezone.utc
            ),
            "url": url,
            "title": title,
            "body": body,
            "responseElapsedTime": content.elapsed.total_seconds(),
            "parseElapsedTime": time() - parse_time,
        }
        return new

if __name__ == "__main__":
    print("START")
    feed = NewFeed()
    reader = NewReader()

    with concurrent.futures.ThreadPoolExecutor() as executor:
        all_executors = []
        for _url in feed.get_urls():
            all_executors.append(executor.submit(
                NewReader().read_new,
                _url
            ))
        all_news = []
        for e in all_executors:
            all_news.append(e.result())

    print(f"{len(all_news)} news")
    for _new in all_news:
        print("-"*15)
        print(f"Date: {_new['insertedDatetime'].isoformat()}")
        print(f"URL: {_new['url']}")
        print(f"Title: {_new['title']}")
        # print(f"Content: {_new['body']}")
        print("-"*15)
    print("END")
