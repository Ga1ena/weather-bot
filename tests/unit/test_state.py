from weatherbot.state import load_last_advice, save_last_advice


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