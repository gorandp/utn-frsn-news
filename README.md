<h1 style="text-align: center">UTN FRSN NEWS</h1>

<img src="./docs/images/logo.jpg" alt="Logo" width="100" style="margin-bottom: 20px; display: block; margin-left: auto; margin-right: auto" />

Webpage (under construction): https://utn.gorandp.com

Telegram Channel: https://t.me/utnfrsnnews

## Introduction

Scripts for data extraction and publishing of the latest news of the faculty in a Telegram channel.

> Telegram Channel: https://t.me/utnfrsnnews

It mainly consists of two scripts:

- Index scraper (extracts URLs of the unprocessed news)
- Main scraper (extracts the content of one news)
- Messenger (send messages via Telegram)

## Index Scraper

Runs every one hour. It has 2 modalities:

- Historic. Goes from the latest page to the current page. It's the slowest modality. Great for populating the DB.
- Live (default). Goes from the current page to the page where it founds the first URL matching a record in DB. Each URL is assumed to be unique and unmutable, that's why we do this approach. It also checks for the older 10 results (we assume the worst case scenario, the page had an error while posting or posted a news which is older than our most recent scrapped news).

After the modality is finished, all results are sorted from oldest to most recent, and inserted into `utn-frsn-news-scraper` queue in that order (so the Main scraper starts with the oldest, and so will be the Messenger).

![Diagram of Index Scraper](/docs/images/indexScraper.drawio.png)

## Main Scraper

It will run only one instance at a time. It is triggered by the `utn-frsn-news-scraper` queue. Extracts the whole news information (title, content, image, date) and metadata (responseElapsedTime, parseElapsedTime).

After extraction, it inserts a task in the `utn-frsn-news-messenger` queue.

![Diagram of Main Scraper](/docs/images/mainScraper.drawio.png)

## Messenger

It will run only one instance at a time. It is triggered by the `utn-frsn-news-messenger` queue. Retrieves the news information from D1 and sends the message via Telegram.

![Diagram of Messenger](/docs/images/messenger.drawio.png)

## DB Structure

Cloudflare D1 is a SQLite database which is hosted in the robust and everywhere available cloudflare network.

We use only one table to store all information related to each news, called simply `news`.

The records structure is the following:

Field | Type | Description
--- | --- | ---
id | INTEGER | Unique identifier of each news
url | VARCHAR(511) | Unique URL identifying this news
title | VARCHAR(127) | Title of the news
body | TEXT | News content
photo | VARCHAR(63) | Image location
photo_url | VARCHAR(127) | Image public URL (to send via Telegram instead of the content)
index_at | TEXT | Moment when the [Index Scraper](#index-scraper) detected this news
inserted_at | TEXT | Moment when the [Main Scraper](#main-scraper) inserted this news
response_elapsed_time | REAL | Seconds taken by the faculty server to complete the HTTP request
parse_elapsed_time | REAL | Seconds taken to parse the HTML

## Queues Structure

### utn-frsn-news-scraper

Scraper queue.

Field | Type | Description
--- | --- | ---
news_url | | News URL
inserted_at | | Insertion date
updated_at | | Update date
status | Integer | 0=unprocessed / 1=success / 99=error

### utn-frsn-news-messenger

Messenger queue.

Field | Type | Description
--- | --- | ---
news_id | Integer | News identifier
inserted_at | | Insertion date
updated_at | | Update date
status | Integer | 0=unprocessed / 1=success / 99=error


## Infrastructure

- Hosting: Cloudflare
  - Cloudflare D1 (main database): https://developers.cloudflare.com/d1/
  - Cloudflare Images: https://developers.cloudflare.com/images/
  - Cloudflare Queues: https://developers.cloudflare.com/queues/
- Plans: Workers Paid + Starter Images

### Evolution

- Hosting Heroku (Scheduler + Task) + MongoDB Atlas. Old README: https://github.com/gorandp/utn-frsn-news/tree/5f98c06
  - Previously it was used by its free tier, but since 2022/11/28 its [free plans were removed](https://help.heroku.com/RSBRUH58/removal-of-heroku-free-product-plans-faq)
  - Nice ecosystem of tools
- Hosting GCP (Cloud Schedule + Cloud Functions + Cloud Build + Pub/Sub) + MongoDB Atlas. Old README: https://github.com/gorandp/utn-frsn-news/tree/f4b86d3
  - Nice ecosystem of tools
  - Free tiers are really generous
  - Pricey SQL (that's why we kept MongoDB Atlas)
  - Configurable via handy Shell scripts
- Hosting Cloudflare (Workers + Queues + D1 + Images): current
  - Highly available and robust network
  - Nice and simple ecosystem of tools
  - Free tiers are really generous
  - Cheap and reliable SQL
  - Configurable via JSON inside the project
  - Promotes usage of `uv` (which is a great python version and packages manager, among other things) for its new Python Workers.

## Environment variables

Private keys like Telegram API Key, are stored as a secret. The approach we do is the following. In development we store the secrets in a `.env` file. For testing we store the secrets in Github actions. For production we store the secrets in the Cloudflare Platform.

```
TELEGRAM_API_KEY="..."
## Defaults
# LOGGER_LEVEL=INFO
```

Currently, there's only one secret, the `TELEGRAM_API_KEY`. The other is an environment configuration. We want only to log the INFO and above logs in production, but on development we want it to show starting from the DEBUG logs.

<!-- Maybe for production we want WARNING as the default LOGGER_LEVEL -->
