from unittest.mock import MagicMock, patch

from app.llm.gemini_client import GeminiClientError
from app.services.instruction_pack_live import (
    _photo_urls_from_payload,
    _run_gemini_vision,
    build_live_instruction_pack_response,
)


def test_photo_urls_prefers_view_url():
    payload = {
        "reference_photo_thumbnail_url": "https://cdn.example/thumb.jpg",
        "reference_photo_view_url": "https://cdn.example/view.jpg",
    }
    assert _photo_urls_from_payload(payload) == [
        "https://cdn.example/view.jpg",
        "https://cdn.example/thumb.jpg",
    ]


def test_run_gemini_vision_retries_second_url():
    client = MagicMock()
    client.describe_reference_photo.side_effect = [
        GeminiClientError("image fetch HTTP 404"),
        {
            "image_description": "Blue shirt",
            "seeker_appearance_hints": "Look for blue shirt",
        },
    ]

    with patch(
        "app.services.instruction_pack_live.GeminiVisionClient",
        return_value=client,
    ):
        result = _run_gemini_vision(
            photo_urls=[
                "https://cdn.example/thumb.jpg",
                "https://cdn.example/view.jpg",
            ],
            verbal="Near gate",
        )

    assert result["seeker_appearance_hints"] == "Look for blue shirt"
    assert client.describe_reference_photo.call_count == 2


def test_live_pack_logs_when_gemini_missing(caplog):
    payload = {
        "verbal_handover_notes": "Near gate",
        "has_reference_photo": True,
        "reference_photo_view_url": "https://cdn.example/view.jpg",
        "lat": 12.94,
        "lng": 80.24,
    }
    mock_groq = {
        "delivery_instructions": "Program line\n\nHandover notes: Near gate",
        "location_description": "Chennai",
        "seeker_handover_hints": "Confirm consent at gate",
    }

    with patch("app.config.settings.gemini_configured", return_value=False):
        with patch("app.config.settings.groq_configured", return_value=True):
            with patch(
                "app.services.instruction_pack_live.GroqClient"
            ) as groq_cls:
                groq_cls.return_value.chat_json.return_value = mock_groq
                with patch(
                    "app.services.instruction_pack_live.reverse_geocode",
                    return_value="Chennai",
                ):
                    with caplog.at_level("WARNING"):
                        result = build_live_instruction_pack_response(payload)

    assert result["source"] == "groq"
    assert result["seeker_appearance_hints"] is None
    assert "GEMINI_API_KEY missing" in caplog.text
