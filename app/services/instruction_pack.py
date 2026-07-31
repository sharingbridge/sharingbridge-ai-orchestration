from __future__ import annotations

import logging

from ..config import settings
from ..llm.safety import LlmUnavailableError, UnsafeContentError, reject_if_unsafe
from ..service_log import log_warn

logger = logging.getLogger("ai-orchestration")


def build_instruction_pack_response(payload: dict) -> dict:
    """Live Groq/Gemini only — never assemble raw user notes when the LLM is down."""
    if not settings.live_llm_enabled():
        raise LlmUnavailableError(
            "AI_LLM_MODE must be live. Raw user-text passthrough is disabled."
        )
    if not settings.groq_configured():
        raise LlmUnavailableError(
            "GROQ_API_KEY is required for live instruction-pack."
        )

    verbal = reject_if_unsafe(
        str(payload.get("verbal_handover_notes") or ""),
        field="verbal_handover_notes",
    )
    safe_payload = {**payload, "verbal_handover_notes": verbal}

    try:
        from .instruction_pack_live import build_live_instruction_pack_response

        return build_live_instruction_pack_response(safe_payload)
    except (LlmUnavailableError, UnsafeContentError):
        raise
    except Exception as exc:
        log_warn(logger, "[instruction-pack] live path failed (fail-closed): %s", exc)
        raise LlmUnavailableError(
            f"Live instruction-pack failed: {exc}"
        ) from exc
