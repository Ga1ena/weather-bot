import json
from pathlib import Path


def load_last_advice(path: Path) -> str | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))["advice"]
    except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError):
        return None


def save_last_advice(path: Path, advice: str) -> None:
    path.write_text(json.dumps({"advice": advice}), encoding="utf-8")