from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.services.program_reference import program_intro_line
from app.services.vendor_urls import build_vendor_search_url

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "ai-orchestration"
    assert "config" in body
    assert "llm_mode" in body["config"]
    assert "groq_configured" in body["config"]


def test_vendor_search_urls():
    z = build_vendor_search_url("Zomato", "Ratna Cafe", "chennai")
    assert "zomato.com/chennai/restaurants" in z
    assert "Ratna" in z
    s = build_vendor_search_url("Swiggy", "Murugan Idli Shop", "chennai")
    assert "swiggy.com/search" in s


def test_suggest_vendors_ranks_by_query():
    mock_result = {
        "suggestions": [
            {
                "restaurant_name": "Murugan Idli Shop",
                "menu_items": ["Dosa"],
                "app_name": "Swiggy",
                "order_url": "https://www.swiggy.com/search?query=Murugan+Idli+Shop",
                "confidence": 0.9,
                "notes": "Pick nearest outlet",
            },
            {
                "restaurant_name": "Ratna Cafe",
                "menu_items": ["Filter Coffee"],
                "app_name": "Zomato",
                "order_url": "https://www.zomato.com/chennai/restaurants?q=Ratna+Cafe",
                "confidence": 0.85,
                "notes": "Breakfast option",
            },
        ],
        "generated_at": "2026-09-27T00:00:00+00:00",
        "source": "groq",
    }
    with patch("app.config.settings.live_llm_enabled", return_value=True), patch(
        "app.config.settings.groq_configured", return_value=True
    ), patch(
        "app.services.suggest_vendors.build_groq_suggest_vendors_response",
        return_value=mock_result,
    ):
        response = client.post(
            "/internal/v1/llm/suggest-vendors",
            json={
                "query_text": "swiggy dosa",
                "location_precision": "gps",
                "lat": 12.97,
                "lng": 80.22,
                "manual_area": "Chennai",
            },
        )
    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "groq"
    assert len(body["suggestions"]) <= 5
    names = [s["restaurant_name"] for s in body["suggestions"]]
    assert "Ratna Cafe" in names or "Murugan Idli Shop" in names
    for item in body["suggestions"]:
        assert "swiggy.com" in item["order_url"] or "zomato.com" in item["order_url"]


def test_program_intro_pending():
    line = program_intro_line("pending")
    assert "not published yet" in line
    assert "http" not in line


def test_program_intro_real_url():
    line = program_intro_line("https://example.org/about")
    assert "https://example.org/about" in line


def test_instruction_pack_courier_facing_only():
    mock_result = {
        "pack_id": "pack-test-1",
        "delivery_instructions": (
            "SharingBridge meal handover (site not published yet).\n\n"
            "Handover notes: Blue shirt near the gate\n\n"
            "Additional details: Look for the blue shirt near the gate."
        ),
        "generated_at": "2026-09-27T00:00:00+00:00",
        "source": "groq",
        "image_description": None,
        "seeker_handover_hints": "Look for blue shirt near gate",
        "location_description": None,
    }
    with patch("app.config.settings.live_llm_enabled", return_value=True), patch(
        "app.config.settings.groq_configured", return_value=True
    ), patch(
        "app.services.instruction_pack_live.build_live_instruction_pack_response",
        return_value=mock_result,
    ):
        response = client.post(
            "/internal/v1/llm/instruction-pack",
            json={
                "verbal_handover_notes": "Blue shirt near the gate",
                "has_reference_photo": True,
                "presets": [
                    {
                        "restaurant_name": "Cafe X",
                        "menu_items": ["Coffee"],
                        "app_name": "Swiggy",
                    }
                ],
            },
        )
    assert response.status_code == 200
    body = response.json()
    text = body["delivery_instructions"]
    assert "not published yet" in text or "SharingBridge" in text
    assert "Blue shirt near the gate" in text
    assert "Handover notes:" in text
    assert "Additional details:" in text
    assert "AI-sensitized" not in text
    assert "saved order shortcuts" not in text.lower()
    assert "Cafe X" not in text
    assert body["pack_id"]
