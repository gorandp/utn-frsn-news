from datetime import timedelta


def get_date_msg(new_data: dict) -> str:
    date = new_data.get("publishedDatetime", new_data["insertedDatetime"])
    date -= timedelta(hours=3) # UTC-03
    date_msg = f'<code>{date.replace(microsecond=0)}</code>'
    if not new_data.get("publishedDatetime"):
        date_msg = date_msg.replace('<code>', '<code>(scrap) ', 1)
    return date_msg


def build_message_header(new_data: dict) -> str:
    out = []
    out.append(get_date_msg(new_data))
    out.append(f'<a href="{new_data["url"]}"><b>{new_data["title"]}</b></a>')
    return "\n".join(out)


def build_message(new_data: dict) -> str:
    out = []
    out.append(get_date_msg(new_data))
    out.append(f'<a href="{new_data["url"]}">'
               f'<b>{new_data["title"]}</b></a>')
    out.append('')
    body = new_data["body"]
    if "&" in body:
        body = body.replace("&", "&amp")
    if "<" in body:
        body = body.replace("<", "&lt")
    if ">" in body:
        body = body.replace(">", "&gt")
    out.append(new_data["body"])
    return "\n".join(out)
