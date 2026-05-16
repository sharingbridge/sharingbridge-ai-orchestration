"""How SharingBridge is named in courier-facing instruction text."""

from __future__ import annotations

_PENDING_VALUES = frozenset(
    {"pending", "placeholder", "tbd", "none", "n/a", "not-published", "not_published"}
)


def program_intro_line(website: str) -> str:
    """
    Build the opening line for delivery instructions.

    SHARINGBRIDGE_WEBSITE_URL may be:
    - ``pending`` (or empty): no public site yet — explicit, not a fake URL
    - ``https://...``: real program website
    - other text: treated as a label, not as a clickable link
    """
    raw = (website or "").strip()
    if not raw or raw.lower() in _PENDING_VALUES:
        return (
            "This meal was arranged through the SharingBridge program "
            "(public website not published yet) for handover to the recipient."
        )
    if raw.startswith("http://") or raw.startswith("https://"):
        return (
            f"This meal was arranged through SharingBridge ({raw}) "
            "for handover to the recipient."
        )
    return (
        f"This meal was arranged through SharingBridge ({raw}) "
        "for handover to the recipient."
    )
