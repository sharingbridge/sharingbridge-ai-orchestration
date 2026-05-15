from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "ai-orchestration"


def test_suggest_vendors_ranks_by_query():
    response = client.post(
        "/internal/v1/llm/suggest-vendors",
        json={
            "query_text": "swiggy dosa",
            "location_precision": "gps",
            "lat": 12.97,
            "lng": 80.22,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["suggestions"]) <= 5
    names = [s["restaurant_name"] for s in body["suggestions"]]
    assert "Ratna Cafe" in names or "Saravana Bhavan" in names


def test_instruction_pack_includes_verbal_notes():
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
    assert "Blue shirt near the gate" in body["delivery_instructions"]
    assert "Cafe X" in body["delivery_instructions"]
    assert body["pack_id"]
