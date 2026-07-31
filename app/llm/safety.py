"""Shared content-safety rules for LLM system prompts and input gates."""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# Client-facing only — never interpolate field names or user text.
_USER_UNSAFE_MESSAGE = "This content cannot be processed."


class UnsafeContentError(ValueError):
    """User-provided text is not allowed for meal-handover flows."""

    def __init__(self, message: str = _USER_UNSAFE_MESSAGE) -> None:
        super().__init__(message)


class LlmUnavailableError(RuntimeError):
    """Live LLM required but unavailable or not configured."""

    def __init__(
        self,
        message: str = "Live LLM is required and is not available.",
    ) -> None:
        super().__init__(message)


# Included in every LLM system prompt (Groq text + Gemini vision).
CONTENT_SAFETY_RULES = """
Content safety (mandatory):
- This product arranges meals with dignity. Refuse sexual, pornographic, violent,
  hateful, harassing, illegal, or exploitative content.
- Do not copy, amplify, or rewrite unsafe user text into restaurant names, menu
  items, notes, or courier instructions.
- If the user input is inappropriate for food delivery / handover, do not invent
  substitutes that preserve the harmful meaning — return empty suggestions or a
  short neutral refusal in the JSON fields instead.
- Never include slurs, graphic violence, sexual content, or instructions to harm.
- Keep language respectful toward initiators, beneficiaries, kitchens, and couriers.
""".strip()


_BLOCKED_PATTERNS = [
    re.compile(r"\b(kill|murder|rape|porn|nude|naked|sex\b|sexual|suicide)\b", re.I),
    re.compile(r"\b(bomb|terrorist|behead)\b", re.I),
]


def reject_if_unsafe(text: str, *, field: str = "input") -> str:
    """Return cleaned text, or raise UnsafeContentError if blocked terms remain.

    ``field`` is for server logs only — never included in the client-facing message,
    and the rejected text is never echoed.
    """
    cleaned = " ".join((text or "").split()).strip()
    if not cleaned:
        return ""
    for pattern in _BLOCKED_PATTERNS:
        if pattern.search(cleaned):
            logger.info("Rejected unsafe content for field=%s", field)
            raise UnsafeContentError()
    return cleaned
