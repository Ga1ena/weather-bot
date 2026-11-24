import os
from functools import partial

import requests

TELEGRAM_API = "https://api.telegram.org"


class NotifyError(RuntimeError):
    pass


def console_notify(text: str) -> None:
    print(text)


def telegram_notify(text: str, token: str, chat_id: str, timeout: int = 10) -> None:
    url = f"{TELEGRAM_API}/bot{token}/sendMessage"
    try:
        response = requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=timeout)
    except requests.RequestException as exc:
        # `from None` и только тип ошибки: в тексте исходных ошибок requests есть URL с токеном
        raise NotifyError(f"Telegram недоступен: {type(exc).__name__}") from None
    if response.status_code != 200:
        raise NotifyError(f"Telegram вернул {response.status_code}: {response.text[:200]}")

def read_credentials() -> tuple[str, str]:
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    missing = [name for name, value in (("TELEGRAM_TOKEN", token),
                                        ("TELEGRAM_CHAT_ID", chat_id)) if not value]
    if missing:
        raise RuntimeError(f"Не заданы переменные окружения: {', '.join(missing)}")
    return token, chat_id


def telegram_from_env():
    token, chat_id = read_credentials()
    return partial(telegram_notify, token=token, chat_id=chat_id)