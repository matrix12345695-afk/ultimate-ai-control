"""Owner's return link, not an API for reading or writing ChatGPT conversations."""
from urllib.parse import urlsplit
from roadmap import setting, set_setting

LABEL="текущий чат внедрения ULTIMATE в Codex"


def bind(conn,url):
    if not isinstance(url,str) or len(url)>500: raise ValueError("invalid chat URL")
    parsed=urlsplit(url)
    if (parsed.scheme!="https" or parsed.hostname!="chatgpt.com" or parsed.port not in (None,443)
        or parsed.username or parsed.password or parsed.query or parsed.fragment
        or "/c/" not in parsed.path or not parsed.path.rsplit("/c/",1)[1]
        or any(ch.isspace() for ch in url)):
        raise ValueError("use the private chatgpt.com conversation URL, not a shared or sign-in link")
    set_setting(conn,"current_chat_url",url)


def current(conn):
    return {"label":LABEL,"url":setting(conn,"current_chat_url"),"automatic_chat_ingestion":False}


def action(conn):
    link=setting(conn,"current_chat_url")
    return "Вернись в "+LABEL+(". "+link if link else ". Ссылка ещё не задана: /chat_bind <ссылка>.")
