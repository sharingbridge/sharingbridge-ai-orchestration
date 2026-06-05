from unittest.mock import MagicMock, patch

from app.llm.gemini_client import GeminiVisionClient


def test_gemini_vision_uses_header_not_query_key():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": (
                                '{"image_description": "blue shirt",'
                                '"seeker_appearance_hints": "look for blue shirt"}'
                            )
                        }
                    ]
                },
                "finishReason": "STOP",
            }
        ]
    }

    client = GeminiVisionClient(api_key="secret-key", model="gemini-2.5-flash")
    with patch("app.llm.gemini_client._fetch_image", return_value=(b"img", "image/jpeg")):
        with patch("httpx.Client") as client_cls:
            instance = client_cls.return_value.__enter__.return_value
            instance.post.return_value = mock_response
            client.describe_reference_photo(image_url="https://cdn.example/photo.jpg")

    call_kwargs = instance.post.call_args.kwargs
    assert "params" not in call_kwargs or not call_kwargs.get("params")
    assert call_kwargs["headers"]["x-goog-api-key"] == "secret-key"
    assert "secret-key" not in instance.post.call_args.args[0]
