from __future__ import annotations

import os

import httpx


def reverse_geocode(lat: float, lng: float) -> str | None:
    """Best-effort place line from coordinates (Nominatim). Returns None on failure."""
    try:
        lat_f = float(lat)
        lng_f = float(lng)
    except (TypeError, ValueError):
        return None

    user_agent = os.getenv(
        "NOMINATIM_USER_AGENT", "SharingBridge-AI-Orchestration/1.0"
    ).strip()

    with httpx.Client(timeout=8.0) as client:
        response = client.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={
                "lat": lat_f,
                "lon": lng_f,
                "format": "json",
                "zoom": 18,
                "addressdetails": 1,
            },
            headers={"User-Agent": user_agent},
        )
    if response.status_code >= 400:
        return None

    data = response.json()
    if not isinstance(data, dict):
        return None

    display = str(data.get("display_name") or "").strip()
    if display:
        return display

    address = data.get("address")
    if isinstance(address, dict):
        parts = [
            address.get("road"),
            address.get("suburb") or address.get("neighbourhood"),
            address.get("city") or address.get("town") or address.get("village"),
        ]
        line = ", ".join(str(p).strip() for p in parts if p)
        return line or None

    return None
