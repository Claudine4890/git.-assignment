import sys

import requests

from app.db import get_conn
from app.services.soil import get_soil


def main():
    sector = sys.argv[1] if len(sys.argv) > 1 else "Kabarore"
    conn = get_conn()

    try:
        s = get_soil(conn, sector)
    except requests.exceptions.HTTPError as e:
        sys.exit(f"SoilGrids returned an error: {e}\nWait a few minutes and try again.")
    except requests.exceptions.RequestException as e:
        sys.exit(f"Cannot reach SoilGrids: {e}")
    except Exception as e:
        sys.exit(f"Error: {e}")

    print(f"Soil for {s['sector']} (from cache: {s['from_cache']})")
    print(f"Source: {s['source']}\n")
    for name, per_depth in s["values"].items():
        print(f"{name} ({s['units'].get(name, '')}):")
        for depth, value in per_depth.items():
            print(f"   {depth}: {value}")
    conn.close()


if __name__ == "__main__":
    main()