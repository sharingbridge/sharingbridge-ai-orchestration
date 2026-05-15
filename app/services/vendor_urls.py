from __future__ import annotations

from typing import Optional
from urllib.parse import quote_plus


def normalize_city(manual_area: Optional[str]) -> str:
    if not manual_area:
        return "chennai"
    token = manual_area.strip().split(",")[0].split()[0].lower()
    return token or "chennai"


def build_vendor_search_url(app_name: str, restaurant_name: str, city: str = "chennai") -> str:
    """Deep link to vendor app search for the restaurant (MVP — not a guaranteed menu URL)."""
    query = quote_plus(restaurant_name.strip())
    app = (app_name or "").strip().lower()
    city_slug = (city or "chennai").strip().lower()
    if app == "zomato":
        return f"https://www.zomato.com/{city_slug}/restaurants?q={query}"
    if app == "swiggy":
        return f"https://www.swiggy.com/search?query={query}"
    return f"https://www.google.com/search?q={query}+{quote_plus(app_name)}+food+delivery"


def enrich_suggestion_urls(suggestions: list[dict], payload: dict) -> list[dict]:
    city = normalize_city(payload.get("manual_area"))
    enriched: list[dict] = []
    for item in suggestions:
        row = dict(item)
        row["order_url"] = build_vendor_search_url(
            row.get("app_name", ""),
            row.get("restaurant_name", ""),
            city,
        )
        enriched.append(row)
    return enriched
