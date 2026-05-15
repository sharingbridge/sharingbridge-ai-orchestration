from __future__ import annotations

from datetime import datetime, timezone

BASE_SUGGESTIONS = [
    {
        "restaurant_name": "A2B",
        "menu_items": ["Mini Meals", "Curd Rice"],
        "order_url": "https://www.zomato.com/chennai/a2b/order",
        "app_name": "Zomato",
        "confidence": 0.92,
        "notes": "Popular around current location",
    },
    {
        "restaurant_name": "Saravana Bhavan",
        "menu_items": ["Idli Sambar", "Pongal"],
        "order_url": "https://www.swiggy.com/city/chennai/saravana-bhavan/order",
        "app_name": "Swiggy",
        "confidence": 0.88,
        "notes": "Strong vegetarian breakfast options",
    },
    {
        "restaurant_name": "Sangeetha Veg",
        "menu_items": ["Lemon Rice Combo", "Bisibele Bath"],
        "order_url": "https://www.zomato.com/chennai/sangeetha/order",
        "app_name": "Zomato",
        "confidence": 0.84,
        "notes": "Good daytime meal options",
    },
    {
        "restaurant_name": "Ratna Cafe",
        "menu_items": ["Filter Coffee", "Ghee Roast Dosa"],
        "order_url": "https://www.swiggy.com/city/chennai/ratna-cafe/order",
        "app_name": "Swiggy",
        "confidence": 0.81,
        "notes": "Classic South Indian breakfast",
    },
    {
        "restaurant_name": "Murugan Idli Shop",
        "menu_items": ["Podi Idli", "Sambar Vada"],
        "order_url": "https://www.zomato.com/chennai/murugan-idli/order",
        "app_name": "Zomato",
        "confidence": 0.79,
        "notes": "Quick idli-focused orders",
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
    suggestions = _rank_suggestions(query) if query else BASE_SUGGESTIONS[:5]
    return {
        "suggestions": suggestions,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "deterministic",
    }
