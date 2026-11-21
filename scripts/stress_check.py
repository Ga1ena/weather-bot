import time
import requests

API_URL = "https://api.open-meteo.com/v1/forecast"
params = {"latitude": 45.25, "longitude": 19.82,
          "current": "temperature_2m", "timezone": "auto"}

bad = 0
for i in range(30):
    r = requests.get(API_URL, params=params, timeout=10)
    if r.status_code != 200 or not r.content:
        bad += 1
        print(i, r.status_code, len(r.content), dict(r.headers))
    time.sleep(0.5)
print(f"bad: {bad} of 30")