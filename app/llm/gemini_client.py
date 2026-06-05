from __future__ import annotations

import base64
import json
from typing import Any

import httpx

from ..config import settings
from .json_utils import parse_json_object


class GeminiClientError(Exception):
    pass


VISION_SYSTEM = """You describe reference photos for meal handover couriers.
Rules:
- Describe visible appearance and context only (clothing, posture, surroundings).
- Do NOT claim legal identity, name, or certainty ("this is person X").
- Do NOT infer medical, criminal, or immigration status.
- Keep each field under 120 words.
Return JSON only: {"image_description": "...", "seeker_appearance_hints": "..."}"""

# Handover photos are consent-based; relax defaults to reduce false SAFETY blocks.
VISION_SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
]


class GeminiVisionClient:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        timeout_s: float = 60.0,
    ) -> None:
        self.api_key = (api_key or settings.gemini_api_key).strip()
        self.model = (model or settings.gemini_vision_model).strip()
        self.timeout_s = timeout_s

    def configured(self) -> bool:
        return bool(self.api_key)

    def describe_reference_photo(
        self,
        *,
        image_url: str,
        verbal_notes: str = "",
    ) -> dict[str, str]:
        if not self.configured():
            raise GeminiClientError("GEMINI_API_KEY is not set")
        url = (image_url or "").strip()
        if not url:
            raise GeminiClientError("image_url is required")

        image_bytes, mime_type = _fetch_image(url, self.timeout_s)
        b64 = base64.standard_b64encode(image_bytes).decode("ascii")

        user_text = "Describe this handover reference photo for a courier."
        if verbal_notes.strip():
            user_text += f"\nDonor notes (context only): {verbal_notes.strip()}"

        endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent"
        )
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"{VISION_SYSTEM}\n\n{user_text}"},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": b64,
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json",
            },
            "safetySettings": VISION_SAFETY_SETTINGS,
        }

        with httpx.Client(timeout=self.timeout_s) as client:
            response = client.post(
                endpoint,
                params={"key": self.api_key},
                json=payload,
            )

        if response.status_code >= 400:
            raise GeminiClientError(
                f"Gemini HTTP {response.status_code}: {response.text[:500]}"
            )

        data = response.json()
        text = _extract_gemini_text(data)
        try:
            parsed = parse_json_object(text)
        except (ValueError, json.JSONDecodeError) as exc:
            raise GeminiClientError(f"invalid JSON from Gemini: {exc}") from exc

        image_description = str(parsed.get("image_description") or "").strip()
        seeker_hints = str(parsed.get("seeker_appearance_hints") or "").strip()
        if not image_description and not seeker_hints:
            raise GeminiClientError("Gemini returned empty vision fields")

        return {
            "image_description": image_description or seeker_hints,
            "seeker_appearance_hints": seeker_hints or image_description,
        }


def _fetch_image(url: str, timeout_s: float) -> tuple[bytes, str]:
    with httpx.Client(timeout=timeout_s, follow_redirects=True) as client:
        response = client.get(url)
    if response.status_code >= 400:
        raise GeminiClientError(f"image fetch HTTP {response.status_code}")
    content_type = (response.headers.get("content-type") or "image/jpeg").split(";")[0]
    mime = content_type if content_type.startswith("image/") else "image/jpeg"
    body = response.content
    if not body:
        raise GeminiClientError("image fetch returned empty body")
    if len(body) > 8 * 1024 * 1024:
        raise GeminiClientError("image too large for vision step")
    return body, mime


def _extract_gemini_text(data: dict[str, Any]) -> str:
    prompt_feedback = data.get("promptFeedback") or {}
    block_reason = prompt_feedback.get("blockReason")
    if block_reason:
        raise GeminiClientError(f"Gemini blocked prompt: {block_reason}")

    candidates = data.get("candidates") or []
    if not candidates:
        raise GeminiClientError("Gemini returned no candidates")

    first = candidates[0]
    finish_reason = first.get("finishReason")
    if finish_reason and finish_reason not in {"STOP", "MAX_TOKENS"}:
        ratings = first.get("safetyRatings") or []
        blocked = [
            r.get("category")
            for r in ratings
            if isinstance(r, dict) and r.get("blocked")
        ]
        detail = f" finishReason={finish_reason}"
        if blocked:
            detail += f" blocked={blocked}"
        raise GeminiClientError(f"Gemini response blocked:{detail}")

    parts = (first.get("content") or {}).get("parts") or []
    chunks: list[str] = []
    for part in parts:
        text = part.get("text")
        if isinstance(text, str) and text.strip():
            chunks.append(text.strip())
    if not chunks:
        raise GeminiClientError("Gemini returned empty text")
    return "\n".join(chunks)
