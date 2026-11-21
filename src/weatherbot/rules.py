from datetime import date
from enum import Enum

TRANSITION_MONTHS = {4, 10}   # апрель, октябрь
WARM_MONTHS = range(5, 10)    # май-сентябрь

AQI_LIMIT = 100    # выше этого окна не открываем
AQI_MARGIN = 10

class Advice(str, Enum):
    OPEN = "open"
    CLOSE = "close"


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


def _by_temperature(temp, prev, season, margin):
    if season == "warm":
        return Advice.OPEN if temp <= 23 else Advice.CLOSE if temp >= 25 else prev
    if season == "transition":
        low, high = 13, 25
        inside = low + margin <= temp <= high - margin
        outside = temp < low or temp > high
        return Advice.OPEN if inside else Advice.CLOSE if outside else prev
    return Advice.OPEN if temp >= 13 else Advice.CLOSE if temp <= 15 else prev  # cold


def decide(temp: float, prev: Advice | None, season: str,
           aqi: float | None = None, margin: float = 1.0) -> Advice | None:
    """Возвращает новый совет, только если он изменился, иначе None."""
    new = _by_temperature(temp, prev, season, margin)
    if aqi is not None:
        if aqi > AQI_LIMIT:
            new = Advice.CLOSE                      # воздух плохой: закрыто
        elif new == Advice.OPEN and prev != Advice.OPEN and aqi > AQI_LIMIT - AQI_MARGIN:
            new = prev                              # воздух на грани: пока не открываем
    return new if new != prev else None