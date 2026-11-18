import sys

from app.db import get_conn
from app.services.geo import save_coordinates, search_place


def main():
    if len(sys.argv) < 2:
        sys.exit("Usage:\n  python -m scripts.set_coordinates Kabarore\n"
                 "  python -m scripts.set_coordinates Kabarore LAT LON")

    sector = sys.argv[1]
    conn = get_conn()

    if len(sys.argv) == 4:
        lat, lon = float(sys.argv[2]), float(sys.argv[3])
        updated = save_coordinates(conn, sector, lat, lon)
        print(f"Saved {lat}, {lon} for {sector} (rows updated: {updated})")
    else:
        results = search_place(sector)
        if not results:
            print("No results. Get the coordinates from Google Maps instead (see below).")
        for x in results:
            print(f"{x['name']} | {x.get('admin1')} | {x.get('admin2')} | "
                  f"{x['latitude']}, {x['longitude']}")

    print("\nCurrent locations:")
    for r in conn.execute("SELECT sector, district, latitude, longitude FROM locations"):
        print(dict(r))
    conn.close()


if __name__ == "__main__":
    main()