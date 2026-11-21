import pytest
import logging
import time
import requests
from dataclasses import dataclass

pytestmark = pytest.mark.integration

API_URL = "https://api.open-meteo.com/v1/forecast"
AIR_API_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
log = logging.getLogger(__name__)

@dataclass
class AirQuality:
    us_aqi: float | None
    pm2_5: float | None
    pm10: float | None

def _fetch_json(url: str, params: dict, attempts: int = 3) -> dict:
    last_exc = None
    for attempt in range(1, attempts + 1):
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as exc:
            last_exc = exc
            log.warning("%s: попытка %s/%s не удалась: %r", url, attempt, attempts, exc)
            time.sleep(attempt)
    raise RuntimeError(f"{url} недоступен после {attempts} попыток") from last_exc

def get_current_temperature(lat: float, lon: float) -> float:
    data = _fetch_json(API_URL, {"latitude": lat, "longitude": lon,
                                 "current": "temperature_2m", "timezone": "auto"})
    return data["current"]["temperature_2m"]

def get_air_quality(lat: float, lon: float) -> AirQuality:
    data = _fetch_json(AIR_API_URL, {"latitude": lat, "longitude": lon,
                                     "current": "us_aqi,pm2_5,pm10", "timezone": "auto"})
    cur = data["current"]
    return AirQuality(cur.get("us_aqi"), cur.get("pm2_5"), cur.get("pm10"))