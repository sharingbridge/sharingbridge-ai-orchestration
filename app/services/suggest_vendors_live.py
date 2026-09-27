from __future__ import annotations

import logging
from datetime import datetime, timezone

from ..llm.groq_client import GroqClient, GroqClientError
from .vendor_urls import enrich_suggestion_urls

from ..llm.safety import CONTENT_SAFETY_RULES

logger = logging.getLogger("ai-orchestration")

SUGGEST_VENDORS_JSON_SCHEMA: dict = {
    "name": "suggest_vendors",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "suggestions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "restaurant_name": {"type": "string"},
                        "menu_items": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "app_name": {"type": "string"},
                        "confidence": {"type": "number"},
                        "notes": {"type": "string"},
                    },
                    "required": [
                        "restaurant_name",
                        "menu_items",
                        "app_name",
                        "confidence",
                        "notes",
                    ],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["suggestions"],
        "additionalProperties": False,
    },
}

SUGGEST_SYSTEM = f"""You help initiators in India find food delivery vendor presets.
Return JSON only matching the required schema with a top-level "suggestions" array.
Rules:
- For normal food, cuisine, restaurant, menu, or area queries, return 1-5 relevant
  suggestions (never an empty list for ordinary searches like "a2b", "dosa",
  "mylapore", "swiggy meals").
- Prefer Zomato or Swiggy as app_name.
- menu_items: 1-3 plausible food items only.
- confidence between 0.5 and 0.99.
- Do not invent guaranteed menu URLs (order_url is added server-side).
- Return "suggestions": [] only when the query is clearly unsafe or not about food
  delivery / vendors at all.

{CONTENT_SAFETY_RULES}
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
    data = client.chat_json(
        system=SUGGEST_SYSTEM,
        user=user,
        json_schema=SUGGEST_VENDORS_JSON_SCHEMA,
    )
    raw_list = data.get("suggestions")
    if not isinstance(raw_list, list):
        keys = sorted(str(k) for k in data.keys())
        logger.warning(
            "[suggest-vendors] Groq JSON missing suggestions list keys=%s",
            keys,
        )
        raise GroqClientError(
            f"Groq response missing suggestions list (keys={keys})"
        )

    if not raw_list:
        # Valid empty answer (unsafe / non-food) — do not 503 / retry.
        logger.info("[suggest-vendors] Groq returned empty suggestions list")
        return {
            "suggestions": [],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": "groq",
        }

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
        logger.warning(
            "[suggest-vendors] Groq suggestions failed row validation count=%s",
            len(raw_list),
        )
        raise GroqClientError("Groq suggestions failed validation")

    suggestions = enrich_suggestion_urls(normalized, payload)
    return {
        "suggestions": suggestions,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "groq",
    }
