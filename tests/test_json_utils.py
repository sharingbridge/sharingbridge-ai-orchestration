from app.llm.json_utils import parse_json_object


def test_parse_json_object_raw():
    assert parse_json_object('{"a": 1}') == {"a": 1}


def test_parse_json_object_fenced():
    raw = """Here is JSON:
```json
{"image_description": "blue shirt"}
```
"""
    assert parse_json_object(raw)["image_description"] == "blue shirt"
