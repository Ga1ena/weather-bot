from datetime import date

import pytest

from weatherbot.client import AirQuality
from weatherbot.main import build_status
from weatherbot.rules import HEATING_ON_MAX, HEATING_OFF_MIN, COLD_CLOSE_MAX, COLD_OPEN_MIN
from weatherbot.state import save_last_advice, save_value


def test_status_in_dead_zone_says_no_new_advice(tmp_path):
    state_file = tmp_path / "state.json"
    save_last_advice(state_file, "close")
    temp = (COLD_CLOSE_MAX + COLD_OPEN_MIN) / 2      # середина промежуточной зоны
    text = build_status(0, 0, state_file, today=date(2026, 11, 16),
                        get_temp=lambda lat, lon: temp,
                        get_air=lambda lat, lon: AirQuality(71, None, None))
    assert "промежуточная зона" in text
    assert "лучше держать окна закрытыми" in text


def test_status_contains_all_parts(tmp_path):
    state_file = tmp_path / "state.json"
    save_last_advice(state_file, "open")
    text = build_status(0, 0, state_file, today=date(2026, 5, 20),
                        get_temp=lambda lat, lon: 18.24,
                        get_air=lambda lat, lon: AirQuality(42, None, None))
    assert "18.2 °C" in text
    assert "AQI 42 (хорошо)" in text
    assert "тёплый" in text
    assert "можно открывать окна" in text


def test_status_without_air_data_and_state(tmp_path):
    def boom(lat, lon):
        raise RuntimeError("down")

    text = build_status(0, 0, tmp_path / "none.json", today=date(2026, 1, 10),
                        get_temp=lambda lat, lon: 5.0, get_air=boom)
    assert "нет данных" in text
    assert "холодный" in text


MID = (HEATING_ON_MAX + HEATING_OFF_MIN) / 2   # середина промежуточной зоны


@pytest.mark.parametrize("temp, saved, expected", [
    (0.8, None, "Отопление: включить"),          # перезапуск без истории
    (HEATING_ON_MAX, None, "Отопление: включить"),
    (HEATING_OFF_MIN, None, "Отопление: выключить"),
    (20.0, None, "Отопление: выключить"),
    (MID, "on", "Отопление: включить"),          # промежуточная зона: держится прошлый
    (MID, "off", "Отопление: выключить"),
    (MID, None, "Отопление: выключить"),         # истории нет: считаем выключенным
])
def test_status_heating_line(tmp_path, temp, saved, expected):
    state_file = tmp_path / "state.json"
    if saved:
        save_value(state_file, "heating", saved)
    text = build_status(0, 0, state_file, today=date(2026, 1, 10),
                        get_temp=lambda lat, lon: temp,
                        get_air=lambda lat, lon: AirQuality(30, None, None))
    assert expected in text


def test_status_has_no_range_notes_or_placeholders(tmp_path):
    text = build_status(0, 0, tmp_path / "none.json", today=date(2026, 1, 10),
                        get_temp=lambda lat, lon: 18.0,
                        get_air=lambda lat, lon: AirQuality(30, None, None))
    assert "≥" not in text and "≤" not in text
    assert "ещё не было" not in text
    assert "Последний совет" not in text      # совета по окнам пока не было
