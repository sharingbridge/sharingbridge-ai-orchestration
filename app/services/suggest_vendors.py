from __future__ import annotations

from datetime import datetime, timezone

from .vendor_urls import enrich_suggestion_urls

BASE_SUGGESTIONS = [
    {
        "restaurant_name": "A2B",
        "menu_items": ["Mini Meals", "Curd Rice"],
        "app_name": "Zomato",
        "confidence": 0.92,
        "notes": "Opens vendor search — pick the correct outlet in the app",
    },
    {
        "restaurant_name": "Saravana Bhavan",
        "menu_items": ["Idli Sambar", "Pongal"],
        "app_name": "Swiggy",
        "confidence": 0.88,
        "notes": "Opens vendor search — pick the correct outlet in the app",
    },
    {
        "restaurant_name": "Sangeetha Veg",
        "menu_items": ["Lemon Rice Combo", "Bisibele Bath"],
        "app_name": "Zomato",
        "confidence": 0.84,
        "notes": "Opens vendor search — pick the correct outlet in the app",
    },
    {
        "restaurant_name": "Ratna Cafe",
        "menu_items": ["Filter Coffee", "Ghee Roast Dosa"],
        "app_name": "Swiggy",
        "confidence": 0.81,
        "notes": "Opens vendor search — pick the correct outlet in the app",
    },
    {
        "restaurant_name": "Murugan Idli Shop",
        "menu_items": ["Podi Idli", "Sambar Vada"],
        "app_name": "Zomato",
        "confidence": 0.79,
        "notes": "Opens vendor search — pick the correct outlet in the app",
    },
]


def _rank_suggestions(query_text: str) -> list[dict]:
    q = query_text.lower()
    scored: list[tuple[float, dict]] = []
    for item in BASE_SUGGESTIONS:
        haystack = " ".join(
            [
                item["restaurant_name"],
                " ".join(item["menu_items"]),
                item["app_name"],
                item.get("notes", ""),
            ]
        ).lower()
        score = 0.0
        for token in q.split():
            if len(token) < 3:
                continue
            if token in haystack:
                score += 1.0
        if "zomato" in q and item["app_name"].lower() == "zomato":
            score += 0.5
        if "swiggy" in q and item["app_name"].lower() == "swiggy":
            score += 0.5
        scored.append((score + item["confidence"] * 0.1, item))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [item for _, item in scored[:5]]


def build_suggest_vendors_response(payload: dict) -> dict:
    query = str(payload.get("query_text") or "").strip()
    ranked = _rank_suggestions(query) if query else BASE_SUGGESTIONS[:5]
    suggestions = enrich_suggestion_urls(ranked, payload)
    return {
        "suggestions": suggestions,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "deterministic",
    }
