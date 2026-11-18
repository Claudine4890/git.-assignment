import sys

import requests

from app.db import get_conn
from app.services.weather import get_weather


def main():
    sector = sys.argv[1] if len(sys.argv) > 1 else "Kabarore"
    conn = get_conn()

    try:
        w = get_weather(conn, sector)
    except requests.exceptions.ConnectionError:
        sys.exit("Cannot reach Open-Meteo from Python (internet or DNS problem). "
                 "Fix the network first, then run this again.")
    except Exception as e:
        sys.exit(f"Error: {e}")

    print(f"Weather for {w['sector']} (from cache: {w['from_cache']})")
    c = w["current"]
    print(f"Now: {c['temperature_c']} C, humidity {c['humidity_pct']}%, rain {c['rain_mm']} mm")
    print(f"Rain in the last 7 days: {w['rain_last_7_days_mm']} mm")
    print(f"Rain expected in the next 7 days: {w['rain_next_7_days_mm']} mm\n")

    for day in w["days"]:
        print(f"{day['date']} | {day['temp_min']}-{day['temp_max']} C | "
              f"rain {day['rain_mm']} mm | chance {day['rain_chance']}%")
    conn.close()


if __name__ == "__main__":
    main()