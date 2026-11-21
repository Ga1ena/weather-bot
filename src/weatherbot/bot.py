import asyncio
import logging

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, filters

from weatherbot import notifier
from weatherbot.config import (CHECK_INTERVAL_SECONDS, LAT, LON, PROJECT_ROOT,
                               STATE_FILE, setup_logging)
from weatherbot.main import build_status, run_once

log = logging.getLogger(__name__)

HELP_TEXT = (
    "Я слежу за погодой и воздухом и подсказываю, когда открывать и закрывать окна.\n\n"
    "/status: что сейчас (температура, воздух, последний совет)\n"
    "/help: эта подсказка"
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_TEXT)


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        text = await asyncio.to_thread(build_status, LAT, LON, STATE_FILE)
    except Exception:
        log.exception("Не удалось собрать статус")
        text = "Не получилось получить данные, попробуй чуть позже."
    await update.message.reply_text(text)


async def periodic_check(context: ContextTypes.DEFAULT_TYPE) -> None:
    notify = context.job.data
    try:
        await asyncio.to_thread(run_once, LAT, LON, STATE_FILE, notify)
    except Exception:
        log.exception("Плановая проверка не удалась")


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    setup_logging()
    token, chat_id = notifier.read_credentials()
    notify = notifier.telegram_from_env()

    app = Application.builder().token(token).build()
    only_me = filters.Chat(chat_id=int(chat_id))
    app.add_handler(CommandHandler(["start", "help"], start, filters=only_me))
    app.add_handler(CommandHandler("status", status, filters=only_me))
    app.job_queue.run_repeating(periodic_check, interval=CHECK_INTERVAL_SECONDS,
                                first=5, data=notify)
    log.info("Бот запущен")
    app.run_polling()


if __name__ == "__main__":
    main()