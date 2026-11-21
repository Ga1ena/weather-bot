import pytest
from datetime import date
from weatherbot.rules import Advice, decide, season_for, aqi_label


@pytest.mark.parametrize("day, expected", [
    (date(2026, 3, 31), "cold"),
    (date(2026, 4, 1), "transition"),    # граница
    (date(2026, 4, 30), "transition"),
    (date(2026, 5, 1), "warm"),          # граница
    (date(2026, 9, 30), "warm"),         # граница
    (date(2026, 10, 1), "transition"),   # граница
    (date(2026, 10, 31), "transition"),
    (date(2026, 11, 1), "cold"),         # граница
    (date(2026, 1, 15), "cold"),
    (date(2026, 7, 15), "warm"),
])
def test_season_for(day, expected):
    assert season_for(day) == expected

@pytest.mark.parametrize("temp, prev, expected", [
    (9.9,  Advice.OPEN,  Advice.CLOSE),   # ниже диапазона
    (10.0, Advice.OPEN,  None),           # граница: остаёмся в «открыто»
    (10.5, Advice.CLOSE, None),           # запас: пока не предлагаем открывать
    (11.0, Advice.CLOSE, Advice.OPEN),    # уверенно внутри
    (18.0, Advice.CLOSE, Advice.OPEN),
    (18.0, Advice.OPEN,  None),
    (24.0, Advice.CLOSE, Advice.OPEN),
    (24.5, Advice.CLOSE, None),           # запас сверху
    (25.0, Advice.OPEN,  None),           # граница: ещё в диапазоне
    (25.1, Advice.OPEN,  Advice.CLOSE),   # выше диапазона
])
def test_decide_transition(temp, prev, expected):
    assert decide(temp, prev, "transition") == expected

def run(temps, season, prev=None):
    """Прогоняет серию замеров, как это делал бы бот, и собирает отправленные советы."""
    sent = []
    for t in temps:
        advice = decide(t, prev, season)
        if advice:
            sent.append(advice)
            prev = advice
    return sent

def test_no_spam_over_a_day():
    temps = [26, 25.5, 24, 23.5, 22.9, 22, 23.5, 24.5, 25.0]
    assert run(temps, "warm") == [Advice.CLOSE, Advice.OPEN, Advice.CLOSE]

@pytest.mark.parametrize("prev, aqi, expected", [
    (Advice.CLOSE, 50,   Advice.OPEN),    # чистый воздух: обычная логика
    (Advice.CLOSE, 90,   Advice.OPEN),    # граница запаса
    (Advice.CLOSE, 91,   None),           # воздух на грани: не открываем
    (Advice.CLOSE, 101,  None),           # и так закрыто, молчим
    (Advice.OPEN,  100,  None),           # ровно 100: «не выше лимита»
    (Advice.OPEN,  101,  Advice.CLOSE),   # окна открыты, воздух испортился
    (None,         150,  Advice.CLOSE),   # первый запуск при плохом воздухе
    (Advice.CLOSE, None, Advice.OPEN),    # данных о воздухе нет: не блокируем
])
def test_decide_with_air_quality(prev, aqi, expected):
    # 18 °C: внутри диапазона переходного сезона, температура сама разрешает открыть
    assert decide(18.0, prev, "transition", aqi=aqi) == expected


@pytest.mark.parametrize("aqi, label", [
    (0, "хорошо"), (50, "хорошо"), (51, "умеренно"), (100, "умеренно"),
    (101, "вредно для чувствительных групп"), (200, "вредно"),
    (300, "очень вредно"), (301, "опасно"),
])
def test_aqi_label(aqi, label):
    assert aqi_label(aqi) == label