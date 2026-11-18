import requests

from app.services.cache import get_cached, set_cached

SOIL_URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"
CACHE_MINUTES = 60 * 24 * 30  # 30 days: soil does not change quickly
PROPERTIES = ["clay", "sand", "silt", "phh2o", "soc", "nitrogen"]
DEPTHS = ["0-5cm", "5-15cm", "15-30cm"]


def get_soil(conn, sector):
    loc = conn.execute(
        "SELECT latitude, longitude FROM locations WHERE sector = ?", (sector,)
    ).fetchone()
    if loc is None:
        raise ValueError(f"Unknown sector: {sector}")
    if loc["latitude"] is None:
        raise ValueError(f"No coordinates saved for {sector}")

    key = f"soil:{sector}"
    cached = get_cached(conn, key, CACHE_MINUTES)
    if cached:
        cached["from_cache"] = True
        return cached

    params = [("lat", loc["latitude"]), ("lon", loc["longitude"]), ("value", "mean")]
    params += [("property", p) for p in PROPERTIES]
    params += [("depth", d) for d in DEPTHS]

    r = requests.get(SOIL_URL, params=params, timeout=60)
    r.raise_for_status()
    layers = r.json()["properties"]["layers"]

    values, units = {}, {}
    for layer in layers:
        name = layer["name"]
        unit = layer.get("unit_measure", {})
        factor = unit.get("d_factor") or 1
        units[name] = unit.get("target_units", "")
        per_depth = {}
        for dep in layer["depths"]:
            mean = dep["values"].get("mean")
            per_depth[dep["label"]] = None if mean is None else round(mean / factor, 2)
        values[name] = per_depth

    result = {
        "sector": sector,
        "values": values,
        "units": units,
        "source": "ISRIC SoilGrids (estimates, not field measurements)",
        "from_cache": False,
    }
    set_cached(conn, key, result)
    return result