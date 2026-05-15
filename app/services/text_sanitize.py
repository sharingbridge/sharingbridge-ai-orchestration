from __future__ import annotations

import re

# MVP policy pass — expand with moderation service later.
_BLOCKED_PATTERNS = [
    re.compile(r"\b(kill|murder|rape)\b", re.IGNORECASE),
]


def sanitize_handover_notes(text: str) -> str:
    """People-friendly handover line for couriers (strips unsafe terms for MVP)."""
    cleaned = " ".join((text or "").split()).strip()
    if not cleaned:
        return ""
    for pattern in _BLOCKED_PATTERNS:
        cleaned = pattern.sub("[removed]", cleaned)
    return cleaned
