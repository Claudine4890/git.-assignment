import requests
from fastapi import FastAPI, HTTPException, Query

from app.db import get_conn
from app.matching import match_providers
from app.services.soil import get_soil
from app.services.weather import get_weather

app = FastAPI(title="Duhuze API", version="0.1")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/sectors")
def sectors():
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT sector, district, latitude, longitude FROM locations ORDER BY sector"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@app.get("/services")
def services():
    conn = get_conn()
    try:
        return [r["name"] for r in conn.execute("SELECT name FROM services ORDER BY id")]
    finally:
        conn.close()


@app.get("/providers/match")
def providers_match(service: str, sector: str, limit: int = Query(3, ge=1, le=10)):
    conn = get_conn()
    try:
        return match_providers(conn, service, sector, limit)
    finally:
        conn.close()


@app.get("/sector/{name}/weather")
def sector_weather(name: str):
    conn = get_conn()
    try:
        return get_weather(conn, name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=502, detail="Weather service unavailable")
    finally:
        conn.close()


@app.get("/sector/{name}/soil")
def sector_soil(name: str):
    conn = get_conn()
    try:
        return get_soil(conn, name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=502, detail="Soil service unavailable")
    finally:
        conn.close()