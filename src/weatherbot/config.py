import logging
from pathlib import Path

LAT, LON = 45.25, 19.82
PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATE_FILE = PROJECT_ROOT / "state.json"
CHECK_INTERVAL_SECONDS = 15 * 60


def quiet_noisy_loggers() -> None:
    # httpx пишет в лог полный URL запроса, а в нём лежит токен бота
    for name in ("httpx", "httpcore"):
        logging.getLogger(name).setLevel(logging.WARNING)


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(PROJECT_ROOT / "bot.log", encoding="utf-8"),
                  logging.StreamHandler()],
    )
    quiet_noisy_loggers()