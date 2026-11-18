import requests

from app.services.cache import get_cached, set_cached

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
CACHE_MINUTES = 180


def get_weather(conn, sector):
    loc = conn.execute(
        "SELECT latitude, longitude FROM locations WHERE sector = ?", (sector,)
    ).fetchone()
    if loc is None:
        raise ValueError(f"Unknown sector: {sector}")
    if loc["latitude"] is None:
        raise ValueError(f"No coordinates saved for {sector}")

    key = f"weather:{sector}"
    cached = get_cached(conn, key, CACHE_MINUTES)
    if cached:
        cached["from_cache"] = True
        return cached

    r = requests.get(
        FORECAST_URL,
        params={
            "latitude": loc["latitude"],
            "longitude": loc["longitude"],
            "current": "temperature_2m,relative_humidity_2m,precipitation",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max",
            "timezone": "Africa/Kigali",
            "past_days": 7,
            "forecast_days": 7,
        },
        timeout=20,
    )
    r.raise_for_status()
    raw = r.json()

    d = raw["daily"]
    days = []
    for i, date in enumerate(d["time"]):
        days.append({
            "date": date,
            "temp_max": d["temperature_2m_max"][i],
            "temp_min": d["temperature_2m_min"][i],
            "rain_mm": d["precipitation_sum"][i],
            "rain_chance": d["precipitation_probability_max"][i],
        })

    today = raw["current"]["time"][:10]
    past = [x for x in days if x["date"] < today]
    upcoming = [x for x in days if x["date"] >= today]

    result = {
        "sector": sector,
        "current": {
            "temperature_c": raw["current"]["temperature_2m"],
            "humidity_pct": raw["current"]["relative_humidity_2m"],
            "rain_mm": raw["current"]["precipitation"],
        },
        "rain_last_7_days_mm": round(sum(x["rain_mm"] or 0 for x in past), 1),
        "rain_next_7_days_mm": round(sum(x["rain_mm"] or 0 for x in upcoming), 1),
        "days": days,
        "source": "Open-Meteo",
        "from_cache": False,
    }
    set_cached(conn, key, result)
    return result