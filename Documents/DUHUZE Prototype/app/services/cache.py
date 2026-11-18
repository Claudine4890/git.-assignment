import json
from datetime import datetime, timedelta, timezone


def get_cached(conn, key, max_age_minutes):
    row = conn.execute(
        "SELECT fetched_at, payload FROM api_cache WHERE key = ?", (key,)
    ).fetchone()
    if row is None:
        return None
    fetched = datetime.fromisoformat(row["fetched_at"])
    if datetime.now(timezone.utc) - fetched > timedelta(minutes=max_age_minutes):
        return None
    return json.loads(row["payload"])


def set_cached(conn, key, data):
    conn.execute(
        "INSERT OR REPLACE INTO api_cache (key, fetched_at, payload) VALUES (?, ?, ?)",
        (key, datetime.now(timezone.utc).isoformat(), json.dumps(data)),
    )
    conn.commit()