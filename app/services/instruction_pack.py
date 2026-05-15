from __future__ import annotations

import uuid
from datetime import datetime, timezone

from ..config import settings


def _format_presets(presets: list[dict]) -> str:
    if not presets:
        return "(No saved presets supplied.)"
    lines: list[str] = []
    for preset in presets:
        name = preset.get("restaurant_name") or "Restaurant"
        app = preset.get("app_name") or "Vendor app"
        items = preset.get("menu_items") or []
        menu = ", ".join(items) if items else "(menu not listed)"
        lines.append(f"- {name} ({app}): {menu}")
    return "\n".join(lines)


def build_instruction_pack_response(payload: dict) -> dict:
    website = settings.website_url
    verbal = (payload.get("verbal_handover_notes") or "").strip()
    has_photo = bool(payload.get("has_reference_photo"))
    photo_id = payload.get("reference_photo_artifact_id")
    lat = payload.get("lat")
    lng = payload.get("lng")
    location_label = (payload.get("location_label") or "").strip()
    donor = (payload.get("donor_display_name") or "the donor").strip()
    seeker = (payload.get("seeker_display_name") or "the person receiving help").strip()
    presets = payload.get("presets") or []

    geo_line = "Geolocation: not provided for this request."
    if lat is not None and lng is not None:
        label = f" ({location_label})" if location_label else ""
        geo_line = f"Geolocation: {lat}, {lng}{label}"

    photo_line = "Reference photo: not attached."
    if has_photo:
        if photo_id:
            photo_line = f"Reference photo artifact: {photo_id} (secure URL pending photo-service)."
        else:
            photo_line = (
                "Reference photo: attached locally; upload to photo-service will provide "
                "a time-limited secure link."
            )

    donor_notes = verbal if verbal else "(none provided)"

    narrative = f"""This order is placed by a donor for a food seeker via SharingBridge ({website}).

{photo_line}
Seeker identification detail: use the handover notes and reference photo only with consent.
{geo_line}

Donor notes (AI-sensitized): {donor_notes}

Delivery instruction: Please proceed to the coordinates above when available. Identify {seeker} using the notes above and, where permitted, the reference photo. Tell them that {donor} placed this order for them and hand over the package. Request consent before taking a delivery photo. Complete acknowledgement in SharingBridge when the real pipeline is connected.

Your saved order shortcuts:
{_format_presets(presets)}

Copy this block into your vendor app's delivery instructions after opening a saved order link."""

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
