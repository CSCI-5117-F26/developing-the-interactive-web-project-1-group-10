import json
import random
from datetime import datetime
from functools import lru_cache
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
# {
# 	"0": "Clear sky",
# 	"1": "Mainly clear",
# 	"2": "Partly cloudy",
# 	"3": "Overcast",
# 	"45": "Fog",
# 	"48": "Depositing rime fog",
# 	"51": "Light drizzle",
# 	"53": "Moderate drizzle",
# 	"55": "Dense drizzle",
# 	"56": "Light freezing drizzle",
# 	"57": "Dense freezing drizzle",
# 	"61": "Slight rain",
# 	"63": "Moderate rain",
# 	"65": "Heavy rain",
# 	"66": "Light freezing rain",
# 	"67": "Heavy freezing rain",
# 	"71": "Slight snowfall",
# 	"73": "Moderate snowfall",
# 	"75": "Heavy snowfall",
# 	"77": "Snow grains",
# 	"80": "Slight rain showers",
# 	"81": "Moderate rain showers",
# 	"82": "Violent rain showers",
# 	"85": "Slight snow showers",
# 	"86": "Heavy snow showers",
# 	"95": "Thunderstorm",
# 	"96": "Thunderstorm with slight hail",
# 	"97": "Heavy thunderstorm",
# 	"99": "Thunderstorm with heavy hail"
# }
MINNEAPOLIS_LATITUDE = 44.9778
MINNEAPOLIS_LONGITUDE = -93.2650
MINNEAPOLIS_TIMEZONE = ZoneInfo("America/Chicago")
RANDOM_WEATHER_CODES = (0, 0, 0, 2, 2, 2, 51, 61, 81, 71, 75, 77, 85, 95, 96, 99)


def _effect_for_weather_code(code):
    if code in {0, 1}:
        return "sun", 20, 0
    if code in {2, 3}:
        return "cloudy", 25, 0
    if code in {45, 48}:
        return "fog", 20, 0
    if code in {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82}:
        intensity = 55 if code in {55, 57, 65, 67, 82} else 35
        return "rain", intensity, 5
    if code in {71, 73, 75, 77, 85, 86}:
        intensity = 50 if code in {75, 86} else 30
        return "snow", intensity, 20
    if code in {95, 96, 97, 99}:
        return "thunderstorm", 45, 5
    return "none", 0, 0


def _fallback_weather(now):
    return {
        "effect": "none",
        "intensity": 0,
        "density": 0,
        "mode": "day" if 7 <= now.hour < 19 else "night",
    }


@lru_cache(maxsize=4)
def _fetch_minneapolis_weather(_hour_key):
    query = urlencode(
        {
            "latitude": MINNEAPOLIS_LATITUDE,
            "longitude": MINNEAPOLIS_LONGITUDE,
            "daily": "weather_code",
            "current": "is_day",
            "timezone": str(MINNEAPOLIS_TIMEZONE),
            "forecast_days": 1,
        }
    )
    request = Request(
        f"{OPEN_METEO_URL}?{query}",
        headers={"User-Agent": "Missions student web app"},
    )

    with urlopen(request, timeout=3) as response:
        forecast = json.load(response)

    code = int(forecast["daily"]["weather_code"][0])
    effect, intensity, density = _effect_for_weather_code(code)

    return {
        "effect": effect,
        "intensity": intensity,
        "density": density,
        "mode": "day" if forecast["current"]["is_day"] else "night",
    }


def get_minneapolis_weather():
    now = datetime.now(MINNEAPOLIS_TIMEZONE)
    hour_key = now.strftime("%Y-%m-%d-%H")

    try:
        return _fetch_minneapolis_weather(hour_key)
    except (OSError, ValueError, KeyError, IndexError, TypeError):
        return _fallback_weather(now)


def get_random_weather(excluded_effect):
    choices = [
        weather
        for code in RANDOM_WEATHER_CODES
        if (weather := _effect_for_weather_code(code))[0] != excluded_effect
    ]
    effect, intensity, density = random.choice(choices)
    now = datetime.now(MINNEAPOLIS_TIMEZONE)

    return {
        "effect": effect,
        "intensity": intensity,
        "density": density,
        "mode": "day" if 7 <= now.hour < 19 else "night",
    }
