import logging
from datetime import date

from dotenv import load_dotenv

from weatherbot import client, notifier, rules, state
from weatherbot.config import LAT, LON, PROJECT_ROOT, STATE_FILE, setup_logging
from weatherbot.rules import Advice, Heating

log = logging.getLogger(__name__)

SEASON_NAMES = {"warm": "тёплый", "transition": "переходный", "cold": "холодный"}
ADVICE_TEXT = {Advice.OPEN: "можно открывать окна", Advice.CLOSE: "лучше держать окна закрытыми"}
ZONE_TEXT = {Advice.OPEN: "можно открывать", Advice.CLOSE: "держать закрытыми",
             None: "промежуточная зона, новых советов нет"}
HEATING_TEXT = {Heating.ON: "включить", Heating.OFF: "выключить"}


def _parse_advice(raw):
    try:
        return Advice(raw) if raw else None
    except ValueError:
        return None


def _parse_heating(raw):
    try:
        return Heating(raw) if raw else None
    except ValueError:
        return None


def measure(lat, lon, get_temp, get_air):
    temp = get_temp(lat, lon)
    try:
        aq = get_air(lat, lon)
    except (RuntimeError, KeyError) as exc:
        log.warning("Нет данных о воздухе, решаем только по температуре: %r", exc)
        aq = client.AirQuality(None, None, None)
    return temp, aq


def build_message(advice, temp, aq):
    action = "Можно открывать окна" if advice == Advice.OPEN else "Закрывайте окна"
    air = ""
    if aq.us_aqi is not None:
        air = f", воздух: AQI {aq.us_aqi:.0f} ({rules.aqi_label(aq.us_aqi)})"
    return f"{action}. Сейчас {temp:.1f} °C{air}."


def build_heating_message(heating, temp):
    if heating == Heating.ON:
        return f"Похолодание до {temp:.1f} °C. Пора включать отопление."
    return f"Потепление до {temp:.1f} °C. Отопление можно выключить."


def build_status(lat, lon, state_path, today=None,
                 get_temp=client.get_current_temperature,
                 get_air=client.get_air_quality) -> str:
    today = today or date.today()
    season = rules.season_for(today)
    temp, aq = measure(lat, lon, get_temp, get_air)
    prev = _parse_advice(state.load_last_advice(state_path))
    heating_prev = _parse_heating(state.load_value(state_path, "heating"))
    if aq.us_aqi is None:
        air = "нет данных"
    else:
        air = f"AQI {aq.us_aqi:.0f} ({rules.aqi_label(aq.us_aqi)})"
        if aq.us_aqi > rules.AQI_LIMIT:
            air += ", окна открывать не стоит"
    zone = ZONE_TEXT[rules.temperature_advice(temp, None, season)]
    lines = [f"Сейчас: {temp:.1f} °C",
             f"Воздух: {air}",
             f"Сезон: {SEASON_NAMES[season]}",
             f"По температуре сейчас: {zone}"]
    if prev is not None:
        lines.append(f"Последний совет: {ADVICE_TEXT[prev]}")
    lines.append(f"Отопление: {HEATING_TEXT[rules.heating_state(temp, heating_prev)]}")
    return "\n".join(lines)


def _check_windows(temp, aq, today, state_path, notify):
    prev = _parse_advice(state.load_last_advice(state_path))
    advice = rules.decide(temp, prev, rules.season_for(today), aqi=aq.us_aqi)
    log.info("Окна: %.1f °C, AQI %s, прошлый совет: %s, новый: %s", temp, aq.us_aqi, prev, advice)
    if advice is None:
        return None
    notify(build_message(advice, temp, aq))            # сначала отправляем...
    state.save_last_advice(state_path, advice.value)   # ...потом запоминаем
    return advice


def _check_heating(temp, state_path, notify):
    prev = _parse_heating(state.load_value(state_path, "heating"))
    heating = rules.decide_heating(temp, prev)
    log.info("Отопление: %.1f °C, прошлый совет: %s, новый: %s", temp, prev, heating)
    if heating is None:
        return None
    notify(build_heating_message(heating, temp))
    state.save_value(state_path, "heating", heating.value)
    return heating


def run_once(lat, lon, state_path, notify, today=None,
             get_temp=client.get_current_temperature,
             get_air=client.get_air_quality) -> Advice | None:
    today = today or date.today()
    temp, aq = measure(lat, lon, get_temp, get_air)
    advice = _check_windows(temp, aq, today, state_path, notify)
    _check_heating(temp, state_path, notify)
    return advice


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    setup_logging()
    try:
        notify = notifier.telegram_from_env()
    except RuntimeError as exc:
        log.warning("%s. Вывожу сообщения в консоль.", exc)
        notify = notifier.console_notify
    run_once(LAT, LON, STATE_FILE, notify)


if __name__ == "__main__":
    main()