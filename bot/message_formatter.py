def build_message_header(new_data: dict) -> str:
    out = []
    out.append(f'<code>{new_data["insertedDatetime"]}</code>')
    out.append(f'<a href="{new_data["url"]}"><b>{new_data["title"]}</b></a>')
    return "\n".join(out)


def build_message(new_data: dict) -> str:
    out = []
    out.append(f'<code>{new_data["insertedDatetime"]}</code>')
    out.append(f'<a href="{new_data["url"]}">'
               f'<b>{new_data["title"]}</b></a>'
    )
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