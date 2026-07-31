from __future__ import annotations

from datetime import datetime, timezone

from .vendor_urls import enrich_suggestion_urls


def _infer_app_name(query_text: str) -> str:
    q = query_text.lower()
    if "swiggy" in q:
        return "Swiggy"
    if "zomato" in q:
        return "Zomato"
    return "Zomato"


def build_passthrough_suggest_vendors_response(payload: dict) -> dict:
    """Echo the user's query as a single search row — no invented restaurants.

    Used when live LLM is off or fails. Hardcoded vendor catalogs must not
    appear on any runtime path (unit-test fixtures only).
    """
    query = str(payload.get("query_text") or "").strip()
    if not query:
        return {
            "suggestions": [],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": "passthrough",
        }

    app_name = _infer_app_name(query)
    row = {
        "restaurant_name": query,
        "menu_items": [query],
        "app_name": app_name,
        "confidence": 1.0,
        "notes": "Your search text — no AI enrichment",
    }
    return {
        "suggestions": enrich_suggestion_urls([row], payload),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "passthrough",
    }


def build_suggest_vendors_response(payload: dict) -> dict:
    from ..config import settings

    if settings.live_llm_enabled():
        try:
            from .suggest_vendors_live import build_groq_suggest_vendors_response

            return build_groq_suggest_vendors_response(payload)
        except Exception:
            pass

    return build_passthrough_suggest_vendors_response(payload)
