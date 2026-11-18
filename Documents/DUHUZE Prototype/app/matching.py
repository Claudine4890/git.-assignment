def match_providers(conn, service, sector, limit=3):
    rows = conn.execute(
        """
        SELECT p.id, p.name, p.contact_person, p.phone, p.notes,
               hl.sector AS home_sector,
               ps.price, ps.price_unit, ps.price_notes,
               p.verified, p.last_confirmed, p.is_test
        FROM providers p
        JOIN provider_services ps ON ps.provider_id = p.id
        JOIN services s ON s.id = ps.service_id
        JOIN provider_areas pa ON pa.provider_id = p.id
        JOIN locations al ON al.id = pa.location_id
        JOIN locations hl ON hl.id = p.location_id
        WHERE s.name = ?
          AND al.sector = ?
          AND p.is_active = 1
          AND ps.available = 1
        ORDER BY
          CASE WHEN hl.sector = ? THEN 0 ELSE 1 END,
          p.verified DESC,
          p.last_confirmed DESC,
          ps.price IS NULL,
          ps.price ASC
        LIMIT ?
        """,
        (service, sector, sector, limit),
    ).fetchall()

    if not rows:
        return {
            "found": False,
            "message": f"No provider found for {service} in {sector}.",
        }
    return {"found": True, "providers": [dict(r) for r in rows]}