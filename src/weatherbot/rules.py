from datetime import date
from enum import Enum

TRANSITION_MONTHS = {4, 10}   # апрель, октябрь
WARM_MONTHS = range(5, 10)    # май-сентябрь

# Пороги температуры, °C. Меняются только здесь.
WARM_OPEN_MAX, WARM_CLOSE_MIN = 23, 25   # тёплый: открыть при <= 23, закрыть при >= 25
LOW, HIGH = 10, 25                       # переходный: окна открыты в диапазоне LOW–HIGH
COLD_OPEN_MIN, COLD_CLOSE_MAX = 13, 10   # холодный: открыть при >= 13, закрыть при <= 10

AQI_LIMIT = 100    # выше этого окна не открываем
AQI_MARGIN = 10    # вернуться к «можно открывать» только при AQI <= 90

HEATING_ON_MAX = 5     # при <= 5 °C советуем включить отопление
HEATING_OFF_MIN = 7    # при >= 7 °C советуем выключить


class Advice(str, Enum):
    OPEN = "open"
    CLOSE = "close"


class Heating(str, Enum):
    ON = "on"
    OFF = "off"


def season_for(day: date) -> str:
    if day.month in TRANSITION_MONTHS:
        return "transition"
    return "warm" if day.month in WARM_MONTHS else "cold"


def aqi_label(aqi: float) -> str:
    for upper, label in ((50, "хорошо"), (100, "умеренно"),
                         (150, "вредно для чувствительных групп"),
                         (200, "вредно"), (300, "очень вредно")):
        if aqi <= upper:
            return label
    return "опасно"


def describe_rule(season: str) -> str:
    if season == "warm":
        return f"открыть при ≤{WARM_OPEN_MAX} °C, закрыть при ≥{WARM_CLOSE_MIN} °C"
    if season == "transition":
        return f"окна открыты, пока {LOW}–{HIGH} °C"
    return f"открыть при ≥{COLD_OPEN_MIN} °C, закрыть при ≤{COLD_CLOSE_MAX} °C"


def temperature_advice(temp: float, prev: Advice | None, season: str,
                       margin: float = 1.0) -> Advice | None:
    """Что говорит одна температура. В промежуточной зоне возвращает prev."""
    if season == "warm":
        return Advice.OPEN if temp <= WARM_OPEN_MAX else Advice.CLOSE if temp >= WARM_CLOSE_MIN else prev
    if season == "transition":
        inside = LOW + margin <= temp <= HIGH - margin
        outside = temp < LOW or temp > HIGH
        return Advice.OPEN if inside else Advice.CLOSE if outside else prev
    return Advice.OPEN if temp >= COLD_OPEN_MIN else Advice.CLOSE if temp <= COLD_CLOSE_MAX else prev


def decide(temp: float, prev: Advice | None, season: str,
           aqi: float | None = None, margin: float = 1.0) -> Advice | None:
    """Возвращает новый совет, только если он изменился, иначе None."""
    new = temperature_advice(temp, prev, season, margin)
    if aqi is not None:
        if aqi > AQI_LIMIT:
            new = Advice.CLOSE                      # воздух плохой: закрыто
        elif new == Advice.OPEN and prev != Advice.OPEN and aqi > AQI_LIMIT - AQI_MARGIN:
            new = prev                              # воздух на грани: пока не открываем
    return new if new != prev else None


def heating_state(temp: float, prev: Heating | None) -> Heating:
    """Какой совет по отоплению действует сейчас (в промежуточной зоне держится прошлый).

    Без истории считаем, что отопление выключено.
    """
    if prev is None:
        prev = Heating.OFF
    if temp <= HEATING_ON_MAX:
        return Heating.ON
    if temp >= HEATING_OFF_MIN:
        return Heating.OFF
    return prev


def decide_heating(temp: float, prev: Heating | None) -> Heating | None:
    """Возвращает новый совет по отоплению, только если он изменился, иначе None.

    Без истории считаем, что отопление выключено: тогда «выключить»
    не приходит, пока не было «включить».
    """
    before = prev if prev is not None else Heating.OFF
    new = heating_state(temp, prev)
    return new if new != before else None