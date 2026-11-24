from weatherbot.state import load_last_advice, save_last_advice, save_value, load_value


def test_missing_file_returns_none(tmp_path):
    assert load_last_advice(tmp_path / "nope.json") is None


def test_roundtrip(tmp_path):
    path = tmp_path / "state.json"
    save_last_advice(path, "open")
    assert load_last_advice(path) == "open"


def test_corrupt_file_returns_none(tmp_path):
    path = tmp_path / "state.json"
    path.write_text("{oops", encoding="utf-8")
    assert load_last_advice(path) is None


def test_save_value_keeps_other_keys(tmp_path):
    path = tmp_path / "state.json"
    save_value(path, "advice", "open")
    save_value(path, "heating", "on")
    assert load_value(path, "advice") == "open"
    assert load_value(path, "heating") == "on"