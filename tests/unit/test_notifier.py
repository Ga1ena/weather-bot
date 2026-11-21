import pytest
import requests

from weatherbot import notifier


class FakeResponse:
    def __init__(self, status_code=200, text="ok"):
        self.status_code = status_code
        self.text = text


def test_sends_expected_request(monkeypatch):
    calls = {}

    def fake_post(url, json, timeout):
        calls.update(url=url, json=json, timeout=timeout)
        return FakeResponse()

    monkeypatch.setattr(notifier.requests, "post", fake_post)
    notifier.telegram_notify("привет", token="123:ABC", chat_id="42")

    assert calls["url"] == "https://api.telegram.org/bot123:ABC/sendMessage"
    assert calls["json"] == {"chat_id": "42", "text": "привет"}
    assert calls["timeout"] == 10


def test_error_status_raises_and_hides_token(monkeypatch):
    monkeypatch.setattr(notifier.requests, "post",
                        lambda url, json, timeout: FakeResponse(401, '{"ok":false,"error_code":401}'))
    with pytest.raises(notifier.NotifyError) as exc:
        notifier.telegram_notify("x", token="123:SECRET", chat_id="42")
    assert "401" in str(exc.value)
    assert "SECRET" not in str(exc.value)


def test_network_error_is_wrapped_and_hides_token(monkeypatch):
    def boom(url, json, timeout):
        raise requests.ConnectionError(f"failed for {url}")

    monkeypatch.setattr(notifier.requests, "post", boom)
    with pytest.raises(notifier.NotifyError) as exc:
        notifier.telegram_notify("x", token="123:SECRET", chat_id="42")
    assert "SECRET" not in str(exc.value)


def test_from_env_requires_variables(monkeypatch):
    monkeypatch.delenv("TELEGRAM_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    with pytest.raises(RuntimeError):
        notifier.telegram_from_env()


def test_from_env_builds_working_notifier(monkeypatch):
    monkeypatch.setenv("TELEGRAM_TOKEN", "123:ABC")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")
    sent = []
    monkeypatch.setattr(notifier, "telegram_notify",
                        lambda text, token, chat_id: sent.append((text, token, chat_id)))
    notifier.telegram_from_env()("hi")
    assert sent == [("hi", "123:ABC", "42")]