import sys
from pathlib import Path

import pandas as pd

from app.db import get_conn

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
EXCEL_FILE = DATA_DIR / "Duhuze_Provider_Information_Simple.xlsx"

# ---- EDIT THESE LINES ----
VERIFIED = 1                  # 1 only if the provider confirmed the information
LAST_CONFIRMED = "2026-11-18"  # date the information was obtained
EXTRA_AREAS = ""              # other sectors served, e.g. "Kiziguro;Muhura"
# --------------------------

SERVICE_MAP = {
    "Improved maize seeds": "Seeds and Fertilizers",
    "Buying maize harvest": "Transportation and Market Services",
}

NEEDED = [
    "Provider Name", "Sector", "Phone Number", "Service / Product", "Variety",
    "Standard Price (RWF/kg)", "Discounted Price (RWF/kg)",
    "Maize Buying Price", "USSD Code", "Notes",
]


def first(series):
    vals = [v.strip() for v in series if v.strip()]
    return vals[0] if vals else ""


def fix_phone(p):
    p = p.strip().replace(" ", "")
    return "0" + p if len(p) == 9 and not p.startswith("0") else p


def load_rows(path):
    raw = pd.read_excel(path, dtype=str).fillna("")
    missing = [c for c in NEEDED if c not in raw.columns]
    if missing:
        sys.exit(f"Missing columns in Excel: {missing}\nColumns found: {list(raw.columns)}")

    for c in NEEDED:
        raw[c] = raw[c].str.strip()

    rows = []
    keys = ["Provider Name", "Sector", "Phone Number", "Service / Product"]
    for (name, sector, phone, product), g in raw.groupby(keys, sort=False):
        if product not in SERVICE_MAP:
            print("No service mapping for:", product)
            continue

        varieties = ", ".join(dict.fromkeys(v for v in g["Variety"] if v))
        standard = first(g["Standard Price (RWF/kg)"])
        discounted = first(g["Discounted Price (RWF/kg)"])
        buying = first(g["Maize Buying Price"])
        ussd = first(g["USSD Code"])
        note = first(g["Notes"])

        parts = []
        if varieties:
            parts.append(f"{product}: {varieties}")
        if discounted:
            parts.append(f"Discounted price {discounted} RWF/kg")
        if buying:
            parts.append(f"Buying price: {buying}")
        if note:
            parts.append(note)

        rows.append({
            "name": name,
            "phone": fix_phone(phone),
            "sector": sector,
            "areas": EXTRA_AREAS,
            "service": SERVICE_MAP[product],
            "price": float(standard) if standard else None,
            "price_unit": "RWF per kg" if standard else "",
            "price_notes": " | ".join(parts),
            "notes": f"USSD: {ussd}" if ussd else "",
        })
    return rows


def import_rows(conn, rows):
    count = 0
    for r in rows:
        areas = {r["sector"]} | {a.strip() for a in r["areas"].split(";") if a.strip()}
        for a in areas:
            conn.execute("INSERT OR IGNORE INTO locations (sector) VALUES (?)", (a,))

        sector_id = conn.execute(
            "SELECT id FROM locations WHERE sector = ?", (r["sector"],)
        ).fetchone()["id"]

        service = conn.execute(
            "SELECT id FROM services WHERE name = ?", (r["service"],)
        ).fetchone()
        if service is None:
            print("Unknown service:", r["service"])
            continue

        found = conn.execute(
            "SELECT id FROM providers WHERE name = ? AND phone = ?",
            (r["name"], r["phone"]),
        ).fetchone()

        if found:
            provider_id = found["id"]
            conn.execute(
                """UPDATE providers
                   SET location_id = ?, notes = ?, verified = ?, last_confirmed = ?
                   WHERE id = ?""",
                (sector_id, r["notes"], VERIFIED, LAST_CONFIRMED, provider_id),
            )
        else:
            cur = conn.execute(
                """INSERT INTO providers
                   (name, phone, location_id, notes, source, verified, is_test, last_confirmed)
                   VALUES (?, ?, ?, ?, 'manual', ?, 0, ?)""",
                (r["name"], r["phone"], sector_id, r["notes"], VERIFIED, LAST_CONFIRMED),
            )
            provider_id = cur.lastrowid

        conn.execute(
            """INSERT OR REPLACE INTO provider_services
               (provider_id, service_id, price, price_unit, price_notes, available)
               VALUES (?, ?, ?, ?, ?, 1)""",
            (provider_id, service["id"], r["price"], r["price_unit"], r["price_notes"]),
        )

        for a in areas:
            loc = conn.execute("SELECT id FROM locations WHERE sector = ?", (a,)).fetchone()
            conn.execute(
                "INSERT OR IGNORE INTO provider_areas (provider_id, location_id) VALUES (?, ?)",
                (provider_id, loc["id"]),
            )
        count += 1

    conn.commit()
    return count


def main():
    if not EXCEL_FILE.exists():
        sys.exit(f"Excel file not found: {EXCEL_FILE}")

    rows = load_rows(EXCEL_FILE)
    conn = get_conn()
    n = import_rows(conn, rows)
    print(f"Imported {n} rows.\n")

    result = conn.execute("""
        SELECT p.name, p.phone, l.sector, s.name AS service,
               ps.price, ps.price_unit, p.verified, p.last_confirmed, p.notes
        FROM providers p
        JOIN locations l ON l.id = p.location_id
        JOIN provider_services ps ON ps.provider_id = p.id
        JOIN services s ON s.id = ps.service_id
    """).fetchall()

    for r in result:
        print(f"{r['name']} | {r['phone']} | {r['sector']} | {r['service']}")
        print(f"   price: {r['price']} {r['price_unit']} | verified={r['verified']} "
              f"| confirmed {r['last_confirmed']} | {r['notes']}")
    conn.close()


if __name__ == "__main__":
    main()