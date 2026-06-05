from __future__ import annotations

import uuid
from datetime import datetime, timezone

from ..config import settings
from ..geo.reverse_geocode import reverse_geocode
from ..llm.gemini_client import GeminiClientError, GeminiVisionClient
from ..llm.groq_client import GroqClient, GroqClientError
from .program_reference import program_intro_line
from .text_sanitize import sanitize_handover_notes

COMPOSE_SYSTEM = """You write courier-facing meal handover instructions for SharingBridge.
Return JSON only:
{
  "location_description": "readable place line",
  "seeker_handover_hints": "2-4 sentences, consent-based, non-definitive identification",
  "delivery_instructions": "full multiline courier text"
}

Rules for delivery_instructions:
- Start with the exact program_intro line provided (first line).
- Include reference photo summary when image_description is provided.
- Include location_description and coordinates when provided.
- Include donor handover notes when provided.
- Include seeker_handover_hints as a clear section.
- End with dignified handover steps (confirm consent, hand over package, confirm in vendor app).
- Do NOT include vendor preset names, menu items, or order URLs.
- Do NOT claim legal identity of the recipient.
"""


def _photo_url_from_payload(payload: dict) -> str:
    for key in (
        "reference_photo_thumbnail_url",
        "reference_photo_view_url",
    ):
        value = payload.get(key)
        if isinstance(value, str) and value.strip().startswith("http"):
            return value.strip()
    return ""


def build_live_instruction_pack_response(payload: dict) -> dict:
    verbal = sanitize_handover_notes((payload.get("verbal_handover_notes") or "").strip())
    lat = payload.get("lat")
    lng = payload.get("lng")
    location_label = (payload.get("location_label") or "").strip()
    donor = (payload.get("donor_display_name") or "the donor").strip()
    seeker = (payload.get("seeker_display_name") or "the person receiving help").strip()
    has_photo = bool(payload.get("has_reference_photo"))

    location_description = ""
    if lat is not None and lng is not None:
        geocoded = reverse_geocode(lat, lng)
        coord = f"{lat}, {lng}"
        if location_label:
            coord += f" ({location_label})"
        location_description = geocoded or f"Coordinates {coord}"

    image_description = ""
    seeker_appearance_hints = ""
    photo_url = _photo_url_from_payload(payload)

    if has_photo and photo_url and settings.gemini_configured():
        try:
            vision = GeminiVisionClient().describe_reference_photo(
                image_url=photo_url,
                verbal_notes=verbal,
            )
            image_description = vision.get("image_description", "")
            seeker_appearance_hints = vision.get("seeker_appearance_hints", "")
        except GeminiClientError:
            pass

    program_intro = program_intro_line(settings.website_url)

    compose_user = "\n".join(
        [
            f"program_intro: {program_intro}",
            f"donor_display_name: {donor}",
            f"seeker_display_name: {seeker}",
            f"location_description_draft: {location_description or 'not provided'}",
            f"coordinates: {lat}, {lng}" if lat is not None and lng is not None else "coordinates: not provided",
            f"handover_notes: {verbal or 'none'}",
            f"image_description: {image_description or 'not provided'}",
            f"seeker_appearance_hints: {seeker_appearance_hints or 'not provided'}",
            f"has_reference_photo: {has_photo}",
        ]
    )

    groq = GroqClient()
    composed = groq.chat_json(system=COMPOSE_SYSTEM, user=compose_user)

    delivery = str(composed.get("delivery_instructions") or "").strip()
    if not delivery:
        raise GroqClientError("Groq returned empty delivery_instructions")

    loc_out = str(composed.get("location_description") or location_description).strip()
    hints_out = str(
        composed.get("seeker_handover_hints") or seeker_appearance_hints
    ).strip()

    pack_id = str(uuid.uuid4())
    return {
        "pack_id": pack_id,
        "delivery_instructions": delivery,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "groq+gemini" if image_description else "groq",
        "donor_display_name": donor,
        "seeker_display_name": seeker,
        "secure_photo_url": photo_url or None,
        "location_description": loc_out or None,
        "image_description": image_description or None,
        "seeker_appearance_hints": seeker_appearance_hints or None,
        "seeker_handover_hints": hints_out or None,
    }
