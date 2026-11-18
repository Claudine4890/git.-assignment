import requests

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"


def search_place(name, country_code="RW", count=10):
    """Return candidate places for a name, so a person can choose the right one."""
    r = requests.get(
        GEOCODING_URL,
        params={"name": name, "count": count, "language": "en", "countryCode": country_code},
        timeout=20,
    )
    r.raise_for_status()
    return r.json().get("results", [])


def save_coordinates(conn, sector, latitude, longitude):
    cur = conn.execute(
        "UPDATE locations SET latitude = ?, longitude = ? WHERE sector = ?",
        (latitude, longitude, sector),
    )
    conn.commit()
    return cur.rowcount