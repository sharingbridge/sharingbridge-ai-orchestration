from __future__ import annotations

import logging
import os

import httpx

from ..service_log import log_info

logger = logging.getLogger("ai-orchestration")

_GEO_CACHE: dict[str, str | None] = {}
_GEO_CACHE_MAX = 64


def reverse_geocode(lat: float, lng: float) -> str | None:
    """Best-effort place line from coordinates (Nominatim). Returns None on failure."""
    try:
        lat_f = float(lat)
        lng_f = float(lng)
    except (TypeError, ValueError):
        return None

    cache_key = f"{lat_f:.4f},{lng_f:.4f}"
    if cache_key in _GEO_CACHE:
        return _GEO_CACHE[cache_key]

    user_agent = os.getenv(
        "NOMINATIM_USER_AGENT", "SharingBridge-AI-Orchestration/1.0"
    ).strip()

    log_info(logger, "[nominatim] reverse geocode request")
    with httpx.Client(timeout=3.0) as client:
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
        if response.status_code == 429:
            logger.warning(
                "[nominatim] rate limited (HTTP 429); using coordinate fallback"
            )
        _remember_geocode(cache_key, None)
        return None

    data = response.json()
    if not isinstance(data, dict):
        return None

    display = str(data.get("display_name") or "").strip()
    if display:
        _remember_geocode(cache_key, display)
        return display

    address = data.get("address")
    if isinstance(address, dict):
        parts = [
            address.get("road"),
            address.get("suburb") or address.get("neighbourhood"),
            address.get("city") or address.get("town") or address.get("village"),
        ]
        line = ", ".join(str(p).strip() for p in parts if p)
        result = line or None
        _remember_geocode(cache_key, result)
        return result

    _remember_geocode(cache_key, None)
    return None


def _remember_geocode(cache_key: str, value: str | None) -> None:
    if len(_GEO_CACHE) >= _GEO_CACHE_MAX:
        _GEO_CACHE.clear()
    _GEO_CACHE[cache_key] = value
