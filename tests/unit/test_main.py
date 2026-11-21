import json
from datetime import date

import pytest

from weatherbot.client import AirQuality
from weatherbot.main import run_once
from weatherbot.rules import Advice


@pytest.fixture
def runner(tmp_path):
    sent = []
    state_file = tmp_path / "state.json"

    def run(temp, aqi=30, today=date(2026, 5, 20), notify=None, get_air=None):
        return run_once(
            45.25, 19.82, state_file,
            notify=notify or sent.append,
            today=today,
            get_temp=lambda lat, lon: temp,
            get_air=get_air or (lambda lat, lon: AirQuality(aqi, None, None)),
        )

    return run, sent, state_file


def test_first_run_sends_and_saves_state(runner):
    run, sent, state_file = runner
    assert run(18.0) == Advice.OPEN          # 20 мая: тёплый сезон, 18 °C
    assert len(sent) == 1
    assert json.loads(state_file.read_text())["advice"] == "open"


def test_no_duplicate_notification(runner):
    run, sent, _ = runner
    run(18.0)
    assert run(18.5) is None                  # ничего не изменилось
    assert len(sent) == 1


def test_state_survives_between_runs(runner):
    run, sent, _ = runner
    run(18.0)                                 # open
    assert run(26.0) == Advice.CLOSE          # жара: close
    assert len(sent) == 2


def test_bad_air_prevents_opening(runner):
    run, sent, _ = runner
    assert run(18.0, aqi=150) == Advice.CLOSE
    assert "Закрывайте" in sent[0]
    assert "AQI 150" in sent[0]


def test_air_failure_does_not_break_temperature_alerts(runner):
    run, sent, _ = runner

    def boom(lat, lon):
        raise RuntimeError("API down")

    assert run(18.0, get_air=boom) == Advice.OPEN
    assert "AQI" not in sent[0]


def test_failed_notification_is_retried_next_run(runner):
    run, sent, state_file = runner

    def broken_notify(text):
        raise ConnectionError("telegram down")

    with pytest.raises(ConnectionError):
        run(18.0, notify=broken_notify)
    assert not state_file.exists()            # состояние не сохранено
    assert run(18.0) == Advice.OPEN           # следующий запуск отправит
    assert len(sent) == 1