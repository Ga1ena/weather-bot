from datetime import date

from weatherbot.client import AirQuality
from weatherbot.main import build_status
from weatherbot.state import save_last_advice


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
    assert "ещё не было" in text