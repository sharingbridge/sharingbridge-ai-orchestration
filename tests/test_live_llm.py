from unittest.mock import MagicMock, patch

from app.services.instruction_pack import build_instruction_pack_response
from app.services.suggest_vendors import build_suggest_vendors_response


def test_groq_suggest_vendors_live_mode():
    payload = {
        "query_text": "swiggy dosa adyar",
        "location_precision": "gps",
        "lat": 12.97,
        "lng": 80.22,
        "manual_area": "Chennai",
    }
    mock_result = {
        "suggestions": [
            {
                "restaurant_name": "Murugan Idli Shop",
                "menu_items": ["Dosa"],
                "app_name": "Swiggy",
                "confidence": 0.9,
                "notes": "Pick nearest outlet",
            }
        ],
        "generated_at": "2026-06-04T00:00:00+00:00",
        "source": "groq",
    }

    with patch("app.config.settings.live_llm_enabled", return_value=True):
        with patch(
            "app.services.suggest_vendors_live.build_groq_suggest_vendors_response",
            return_value=mock_result,
        ) as groq_build:
            result = build_suggest_vendors_response(payload)

    groq_build.assert_called_once_with(payload)
    assert result["source"] == "groq"
    assert result["suggestions"][0]["restaurant_name"] == "Murugan Idli Shop"


def test_instruction_pack_live_mode():
    payload = {
        "verbal_handover_notes": "Near the gate",
        "has_reference_photo": True,
        "reference_photo_thumbnail_url": "https://cdn.example/thumb.jpg",
        "lat": 12.94,
        "lng": 80.24,
    }
    mock_result = {
        "pack_id": "pack-live-1",
        "delivery_instructions": "Program line\n\nHandover notes: Near the gate",
        "generated_at": "2026-06-04T00:00:00+00:00",
        "source": "groq+gemini",
        "image_description": "Person in blue shirt",
        "seeker_handover_hints": "Look for blue shirt near gate",
        "location_description": "Adyar, Chennai",
    }

    with patch("app.config.settings.live_llm_enabled", return_value=True):
        with patch(
            "app.services.instruction_pack_live.build_live_instruction_pack_response",
            return_value=mock_result,
        ) as live_build:
            result = build_instruction_pack_response(payload)

    live_build.assert_called_once_with(payload)
    assert result["source"] == "groq+gemini"
    assert "Near the gate" in result["delivery_instructions"]


def test_live_mode_falls_back_to_deterministic_on_error():
    payload = {
        "query_text": "zomato meals",
        "location_precision": "manual",
        "manual_area": "Chennai",
    }
    with patch("app.config.settings.live_llm_enabled", return_value=True):
        with patch(
            "app.services.suggest_vendors_live.build_groq_suggest_vendors_response",
            side_effect=RuntimeError("groq down"),
        ):
            result = build_suggest_vendors_response(payload)
    assert result["source"] == "deterministic"
    assert len(result["suggestions"]) <= 5


def test_groq_client_chat_json_parses_response():
    from app.llm.groq_client import GroqClient

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": '{"ok": true}'}}]
    }

    client = GroqClient(api_key="test-key")
    with patch("httpx.Client") as client_cls:
        instance = client_cls.return_value.__enter__.return_value
        instance.post.return_value = mock_response
        parsed = client.chat_json(system="sys", user="user")

    assert parsed == {"ok": True}
