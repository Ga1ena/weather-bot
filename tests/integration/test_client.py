import pytest
import requests

from weatherbot.client import API_URL, get_current_temperature, get_air_quality

lat, lon = 45.25, 19.82
params = {'latitude': lat, 'longitude': lon,
          'current': 'temperature_2m', 'timezone': 'auto'}


@pytest.fixture
def api_response():
    return requests.get(API_URL, params=params, timeout=10)

def test_api_returns_200(api_response):
    assert api_response.status_code == 200

def test_response_contract(api_response):
    body = api_response.json()
    assert body['current_units']['temperature_2m'] == '°C'
    assert isinstance(body['current']['temperature_2m'], (int, float))

def test_temperature_is_plausible():
    temp = get_current_temperature(lat, lon)
    assert -55 <= temp <= 55

def test_response_coordinates_close_to_requested(api_response):
    body = api_response.json()
    assert abs(body["latitude"] - lat) < 0.1
    assert abs(body["longitude"] - lon) < 0.1

def test_air_quality_contract():
    aq = get_air_quality(lat, lon)
    assert aq.us_aqi is None or 0 <= aq.us_aqi <= 500
    assert aq.pm2_5 is None or aq.pm2_5 >= 0

'''def test_debug():
    r = requests.get(API_URL, params=params, timeout=10)
    print(r.status_code, r.url, dict(r.headers), repr(r.text[:300]), sep="\n")'''