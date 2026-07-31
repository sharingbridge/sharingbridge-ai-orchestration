"""Handover-note helpers — prefer reject_if_unsafe for fail-closed gates."""

from __future__ import annotations

from ..llm.safety import UnsafeContentError, reject_if_unsafe


def sanitize_handover_notes(text: str) -> str:
    """Clean whitespace; raise UnsafeContentError if blocked terms are present."""
    return reject_if_unsafe(text, field="verbal_handover_notes")


__all__ = ["sanitize_handover_notes", "UnsafeContentError", "reject_if_unsafe"]
