# RF-Tar-Railt feat(qqapi): new at-user & at-everyone FROM: https://github.com/GraiaProject/Avilla/blob/master/avilla/qqapi/utils.py
import json
import re


def escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def unescape(s: str) -> str:
    return s.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")


def handle_text(msg: str):
    result = []
    text_begin = 0
    msg = msg.replace("@everyone", "")
    msg = re.sub(r"\<qqbot-at-everyone\s/\>", "", msg)
    for embed in re.finditer(
        r"\<(?P<type>(?:@|#|emoji:))!?(?P<id>\w+?)\>|\<(?P<type1>qqbot-at-user) id=\"(?P<id1>\w+)\"\s/\>",
        msg,
    ):
        if content := msg[text_begin : embed.pos + embed.start()]:
            result.append({"type": "text", "text": unescape(content)})
        text_begin = embed.pos + embed.end()
        if embed["type"] == "@":
            result.append({"type": "mention_user", "user_id": embed.group("id")})
        elif embed["type"] == "#":
            result.append({"type": "mention_channel", "channel_id": embed.group("id")})
        elif embed["type"] == "emoji":
            result.append({"type": "emoji", "id": embed.group("id")})
        elif embed["type1"] == "qqbot-at-user":
            result.append({"type": "mention_user", "user_id": embed.group("id1")})
    if content := msg[text_begin:]:
        result.append({"type": "text", "text": unescape(content)})
    return {"messages": json.dumps(result)}


def form_data(message: dict):
    if not (file_image := message.pop("file_image", None)):
        return "post", message
    files = {"file_image": {"value": file_image, "content_type": None, "filename": "file_image"}}
    data_ = {}
    for key, value in message.items():
        if isinstance(value, (list, dict)):
            files[key] = {
                "value": json.dumps({key: value}).encode("utf-8"),
                "content_type": "application/json",
                "filename": f"{key}.json",
            }
        else:
            data_[key] = value
    return "multipart", {"files": files, "data": data_}


def remove_empty(d: dict):
    return {k: (remove_empty(v) if isinstance(v, dict) else v) for k, v in d.items() if v is not None}