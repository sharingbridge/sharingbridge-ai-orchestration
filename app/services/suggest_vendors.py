from __future__ import annotations

from ..config import settings
from ..llm.groq_client import GroqClientError
from ..llm.safety import LlmUnavailableError, UnsafeContentError, reject_if_unsafe
from .suggest_vendors_live import build_groq_suggest_vendors_response


def build_suggest_vendors_response(payload: dict) -> dict:
    """Live Groq only — never echo raw user text when the LLM is down."""
    if not settings.live_llm_enabled():
        raise LlmUnavailableError(
            "AI_LLM_MODE must be live. Raw user-text passthrough is disabled."
        )
    if not settings.groq_configured():
        raise LlmUnavailableError("GROQ_API_KEY is required for live suggest-vendors.")

    query = reject_if_unsafe(
        str(payload.get("query_text") or ""),
        field="query_text",
    )
    if not query:
        raise GroqClientError("query_text is required.")

    safe_payload = {**payload, "query_text": query}
    try:
        return build_groq_suggest_vendors_response(safe_payload)
    except (LlmUnavailableError, UnsafeContentError):
        raise
    except Exception as exc:
        raise LlmUnavailableError(
            f"Live suggest-vendors failed: {exc}"
        ) from exc
