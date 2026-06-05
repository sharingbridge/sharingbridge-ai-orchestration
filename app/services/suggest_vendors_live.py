from __future__ import annotations

from datetime import datetime, timezone

from ..llm.groq_client import GroqClient, GroqClientError
from .vendor_urls import enrich_suggestion_urls

SUGGEST_SYSTEM = """You help donors in India find food delivery vendor presets.
Return JSON only with this shape:
{
  "suggestions": [
    {
      "restaurant_name": "string",
      "menu_items": ["item1", "item2"],
      "app_name": "Zomato or Swiggy",
      "confidence": 0.0,
      "notes": "short hint for donor"
    }
  ]
}
Rules:
- Return at most 5 suggestions ranked by relevance.
- Prefer Zomato or Swiggy as app_name.
- menu_items: 1-3 plausible items.
- confidence between 0.5 and 0.99.
- Do not invent guaranteed menu URLs (order_url is added server-side).
"""


def build_groq_suggest_vendors_response(payload: dict) -> dict:
    query = str(payload.get("query_text") or "").strip()
    if not query:
        raise GroqClientError("query_text is required for Groq suggest-vendors")

    location_bits: list[str] = []
    if payload.get("manual_area"):
        location_bits.append(f"manual_area: {payload['manual_area']}")
    if payload.get("lat") is not None and payload.get("lng") is not None:
        location_bits.append(
            f"coordinates: {payload['lat']}, {payload['lng']} "
            f"({payload.get('location_precision') or 'unknown'})"
        )

    user = f"Donor search query: {query}"
    if location_bits:
        user += "\nLocation context: " + "; ".join(location_bits)

    client = GroqClient()
    data = client.chat_json(system=SUGGEST_SYSTEM, user=user)
    raw_list = data.get("suggestions")
    if not isinstance(raw_list, list) or not raw_list:
        raise GroqClientError("Groq returned no suggestions")

    normalized: list[dict] = []
    for item in raw_list[:5]:
        if not isinstance(item, dict):
            continue
        name = str(item.get("restaurant_name") or "").strip()
        app_name = str(item.get("app_name") or "Zomato").strip()
        if not name:
            continue
        menu_raw = item.get("menu_items")
        menu_items = (
            [str(m).strip() for m in menu_raw if str(m).strip()]
            if isinstance(menu_raw, list)
            else []
        )
        confidence_raw = item.get("confidence")
        try:
            confidence = float(confidence_raw)
        except (TypeError, ValueError):
            confidence = 0.75
        confidence = max(0.5, min(0.99, confidence))
        normalized.append(
            {
                "restaurant_name": name,
                "menu_items": menu_items[:3] or ["Meals"],
                "app_name": app_name,
                "confidence": round(confidence, 2),
                "notes": str(item.get("notes") or "Opens vendor search in the app").strip(),
            }
        )

    if not normalized:
        raise GroqClientError("Groq suggestions failed validation")

    suggestions = enrich_suggestion_urls(normalized, payload)
    return {
        "suggestions": suggestions,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "groq",
    }
