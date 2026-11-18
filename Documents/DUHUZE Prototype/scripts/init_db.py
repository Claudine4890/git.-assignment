from app.db import get_conn

SCHEMA = """
CREATE TABLE IF NOT EXISTS services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sector TEXT NOT NULL UNIQUE,
    district TEXT NOT NULL DEFAULT 'Gatsibo',
    latitude REAL,
    longitude REAL
);

CREATE TABLE IF NOT EXISTS providers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    contact_person TEXT,
    phone TEXT,
    location_id INTEGER,
    equipment TEXT,
    capacity TEXT,
    working_hours TEXT,
    qualifications TEXT,
    notes TEXT,
    source TEXT DEFAULT 'manual',
    verified INTEGER DEFAULT 0,
    is_test INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    last_confirmed TEXT,
    FOREIGN KEY (location_id) REFERENCES locations(id)
);

CREATE TABLE IF NOT EXISTS provider_services (
    provider_id INTEGER NOT NULL,
    service_id INTEGER NOT NULL,
    price REAL,
    price_unit TEXT,
    price_notes TEXT,
    available INTEGER DEFAULT 1,
    PRIMARY KEY (provider_id, service_id),
    FOREIGN KEY (provider_id) REFERENCES providers(id),
    FOREIGN KEY (service_id) REFERENCES services(id)
);

CREATE TABLE IF NOT EXISTS provider_areas (
    provider_id INTEGER NOT NULL,
    location_id INTEGER NOT NULL,
    PRIMARY KEY (provider_id, location_id),
    FOREIGN KEY (provider_id) REFERENCES providers(id),
    FOREIGN KEY (location_id) REFERENCES locations(id)
);

CREATE TABLE IF NOT EXISTS api_cache (
    key TEXT PRIMARY KEY,
    fetched_at TEXT NOT NULL,
    payload TEXT NOT NULL
);
"""

SERVICES = [
    "Land Preparation",
    "Seeds and Fertilizers",
    "Irrigation Services",
    "Pest and Disease Control",
    "Harvesting Services",
    "Post-Harvest Services",
    "Transportation and Market Services",
]


def main():
    conn = get_conn()
    conn.executescript(SCHEMA)
    conn.executemany(
        "INSERT OR IGNORE INTO services (name) VALUES (?)",
        [(s,) for s in SERVICES],
    )
    conn.commit()

    tables = [r["name"] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    print("Tables:", tables)
    print("Services:", conn.execute("SELECT COUNT(*) FROM services").fetchone()[0])
    print("Locations:", conn.execute("SELECT COUNT(*) FROM locations").fetchone()[0])
    conn.close()


if __name__ == "__main__":
    main()