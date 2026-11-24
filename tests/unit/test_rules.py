import pytest
from datetime import date
from weatherbot.rules import (Advice, aqi_label, decide, LOW, HIGH, season_for, decide_heating, Heating, COLD_OPEN_MIN,
                              COLD_CLOSE_MAX, WARM_OPEN_MAX, WARM_CLOSE_MIN, describe_rule, heating_state)

MARGIN = 1.0   # запас по умолчанию в decide()
MID = (LOW + HIGH) / 2

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
    (COLD_OPEN_MIN,       Advice.CLOSE, Advice.OPEN),    # граница: открыть
    (COLD_OPEN_MIN - 0.1, Advice.CLOSE, None),           # промежуточная зона
    (COLD_CLOSE_MAX + 0.1, Advice.OPEN, None),
    (COLD_CLOSE_MAX,      Advice.OPEN,  Advice.CLOSE),   # граница: закрыть
    (COLD_CLOSE_MAX - 5,  Advice.CLOSE, None),           # и так закрыто
])
def test_decide_cold(temp, prev, expected):
    assert decide(temp, prev, "cold") == expected


@pytest.mark.parametrize("temp, prev, expected", [
    (WARM_OPEN_MAX, Advice.CLOSE, Advice.OPEN),
    ((WARM_OPEN_MAX + WARM_CLOSE_MIN) / 2, Advice.CLOSE, None),
    (WARM_CLOSE_MIN, Advice.OPEN, Advice.CLOSE),
    (WARM_CLOSE_MIN, Advice.CLOSE, None),
])
def test_decide_warm(temp, prev, expected):
    assert decide(temp, prev, "warm") == expected


@pytest.mark.parametrize("temp, prev, expected", [
    (LOW - 0.1,   Advice.OPEN,  Advice.CLOSE),   # ниже диапазона
    (LOW,         Advice.OPEN,  None),           # граница: остаёмся в «открыто»
    (LOW + 0.5,   Advice.CLOSE, None),           # запас: пока не предлагаем открывать
    (LOW + MARGIN, Advice.CLOSE, Advice.OPEN),   # уверенно внутри
    (MID,         Advice.CLOSE, Advice.OPEN),
    (MID,         Advice.OPEN,  None),
    (HIGH - MARGIN, Advice.CLOSE, Advice.OPEN),
    (HIGH - 0.5,  Advice.CLOSE, None),           # запас сверху
    (HIGH,        Advice.OPEN,  None),           # граница: ещё в диапазоне
    (HIGH + 0.1,  Advice.OPEN,  Advice.CLOSE),   # выше диапазона
])

def test_decide_transition(temp, prev, expected):
    assert decide(temp, prev, "transition") == expected


def test_cold_season_dead_zone_keeps_previous_advice():
    mid = (COLD_CLOSE_MAX + COLD_OPEN_MIN) / 2
    assert decide(mid, Advice.CLOSE, "cold", aqi=71) is None
    assert decide(mid, Advice.OPEN, "cold", aqi=71) is None


def test_describe_rule_cold_mentions_thresholds():
    assert f"≥{COLD_OPEN_MIN}" in describe_rule("cold")
    assert f"≤{COLD_CLOSE_MAX}" in describe_rule("cold")


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


@pytest.mark.parametrize("temp, prev, expected", [
    (5.0,  None,         Heating.ON),    # граница: включить
    (4.9,  Heating.OFF,  Heating.ON),
    (5.0,  Heating.ON,   None),          # уже включено, не повторяем
    (6.0,  Heating.ON,   None),          # промежуточная зона: ждём
    (6.0,  Heating.OFF,  None),
    (6.9,  Heating.ON,   None),
    (7.0,  Heating.ON,   Heating.OFF),   # граница: выключить
    (7.0,  Heating.OFF,  None),
    (20.0, None,         None),          # тепло, отопление не включали: молчим
])
def test_decide_heating(temp, prev, expected):
    assert decide_heating(temp, prev) == expected


def test_heating_cycle_over_a_cold_snap():
    state, sent = None, []
    for t in [9, 7.5, 6, 5.2, 4.8, 4, 5.5, 6.5, 6.9, 7.0, 8, 5.0]:
        new = decide_heating(t, state)
        if new:
            sent.append(new)
            state = new
    assert sent == [Heating.ON, Heating.OFF, Heating.ON]


@pytest.mark.parametrize("temp, prev, expected", [
    (4.0, None,         Heating.ON),
    (4.0, Heating.OFF,  Heating.ON),
    (8.0, None,         Heating.OFF),
    (8.0, Heating.ON,   Heating.OFF),
    (6.0, None,         Heating.OFF),    # без истории считаем выключенным
    (6.0, Heating.ON,   Heating.ON),     # промежуточная зона: держится прошлый
    (6.0, Heating.OFF,  Heating.OFF),
])
def test_heating_state(temp, prev, expected):
    assert heating_state(temp, prev) == expected