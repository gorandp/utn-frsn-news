from datetime import timedelta

from ..database_models import News


def get_date_msg(news: News) -> str:
    date = news.origin_created_at or news.inserted_at
    date -= timedelta(hours=3)  # UTC-03
    date_msg = f"<code>{date.replace(microsecond=0)}</code>"
    if not news.origin_created_at:
        date_msg = date_msg.replace("<code>", "<code>(scrap) ", 1)
    return date_msg


def build_message_header(news: News) -> str:
    out = []
    out.append(get_date_msg(news))
    out.append(f'<a href="{news.url}"><b>{news.title}</b></a>')
    return "\n".join(out)


def build_message(news: News) -> str:
    out = []
    out.append(get_date_msg(news))
    out.append(f'<a href="{news.url}"><b>{news.title}</b></a>')
    out.append("")
    body = news.content
    if "&" in body:
        body = body.replace("&", "&amp")
    if "<" in body:
        body = body.replace("<", "&lt")
    if ">" in body:
        body = body.replace(">", "&gt")
    out.append(body)
    return "\n".join(out)
