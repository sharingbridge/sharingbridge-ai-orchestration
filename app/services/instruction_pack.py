from __future__ import annotations

import uuid
from datetime import datetime, timezone

from ..config import settings
from .text_sanitize import sanitize_handover_notes


def build_instruction_pack_response(payload: dict) -> dict:
    website = settings.website_url
    verbal = sanitize_handover_notes((payload.get("verbal_handover_notes") or "").strip())
    has_photo = bool(payload.get("has_reference_photo"))
    photo_id = payload.get("reference_photo_artifact_id")
    lat = payload.get("lat")
    lng = payload.get("lng")
    location_label = (payload.get("location_label") or "").strip()
    donor = (payload.get("donor_display_name") or "the donor").strip()
    seeker = (payload.get("seeker_display_name") or "the person receiving help").strip()

    geo_line = "Location: confirm with recipient; coordinates not provided."
    if lat is not None and lng is not None:
        label = f" ({location_label})" if location_label else ""
        geo_line = f"Location: {lat}, {lng}{label}"

    photo_line = "Reference photo: not provided."
    if has_photo:
        if photo_id:
            photo_line = f"Reference photo: see secure link {photo_id} (time-limited)."
        else:
            photo_line = "Reference photo: available to delivery partner per app policy."

    lines = [
        f"This meal was arranged through SharingBridge ({website}) for handover to the recipient.",
        "",
        photo_line,
        geo_line,
    ]

    if verbal:
        lines.extend(["", f"Handover notes: {verbal}"])

    lines.extend(
        [
            "",
            "Additional details:",
            "",
            "",
            f"Please deliver to the location above. Identify {seeker} using the handover notes",
            f"and reference photo only with their consent. This order was placed by {donor} for them.",
            "Hand over the package and confirm delivery in the vendor app.",
        ]
    )

    narrative = "\n".join(lines)

    pack_id = str(uuid.uuid4())
    return {
        "pack_id": pack_id,
        "delivery_instructions": narrative.strip(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "deterministic",
        "donor_display_name": donor,
        "seeker_display_name": seeker,
        "secure_photo_url": None,
    }
