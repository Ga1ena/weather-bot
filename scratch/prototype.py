import requests

lat = 45.25
lon = 19.82

def intro(func):
    def wrapper(*args, **kwargs):
        print('Data aggregation…')
        return func(*args, **kwargs)

    return wrapper

class Weather:
    def __init__(self, latitude, longitude):
        self.lat = latitude
        self.lon = longitude
        self.data = self.get_weather()
        self.temperature = self.data['current']['temperature_2m']

    @intro
    def get_weather(self):
        response = requests.get(
            f'https://api.open-meteo.com/v1/forecast?latitude={self.lat}&longitude={self.lon}&current=temperature_2m&timezone=auto')
        return response.json()

    def warm_or_cold(self):
        if self.temperature < 10:
            return 'Cold. Close the windows!'
        elif 10 <= self.temperature <= 23:
            return 'Warm. Open the windows!'
        else:
            return 'Hot. Close the windows!'

weather = Weather(lat, lon)
print('Current temperature:', weather.temperature)
print(weather.warm_or_cold())