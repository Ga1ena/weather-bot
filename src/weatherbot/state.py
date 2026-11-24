import json
from pathlib import Path


def _read(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def load_value(path: Path, key: str) -> str | None:
    value = _read(path).get(key)
    return value if isinstance(value, str) else None


def save_value(path: Path, key: str, value: str) -> None:
    data = _read(path)   # читаем, меняем один ключ, остальные не трогаем
    data[key] = value
    path.write_text(json.dumps(data), encoding="utf-8")


def load_last_advice(path: Path) -> str | None:
    return load_value(path, "advice")


def save_last_advice(path: Path, advice: str) -> None:
    save_value(path, "advice", advice)