# weather-bot

![tests](https://github.com/Ga1ena/weather-bot/actions/workflows/tests.yml/badge.svg)

Telegram-бот, который следит за температурой и качеством воздуха (AQI)
и подсказывает, когда открывать и закрывать окна. Команда `/status`
показывает текущую ситуацию.

## Запуск
1. `python -m venv .venv` и активировать окружение
2. `pip install -r requirements.txt`
3. Скопировать `.env.example` в `.env` и заполнить токен бота и chat_id
4. Бот: `PYTHONPATH=src python -m weatherbot.bot`
   (в PowerShell: `$env:PYTHONPATH="src"; python -m weatherbot.bot`)

## Тесты
`pytest` (все), `pytest tests/unit` (быстрые, без сети)

## Структура
- `src/weatherbot/rules.py`: чистая логика решений (сезоны, пороги, гистерезис)
- `client.py`: запросы к Open-Meteo, `notifier.py`: Telegram, `state.py`: состояние
- `tests/unit` и `tests/integration`

## Данные
Погода и качество воздуха: [Open-Meteo](https://open-meteo.com).
Данные о воздухе: Copernicus Atmosphere Monitoring Service (CAMS).