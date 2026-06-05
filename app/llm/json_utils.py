from __future__ import annotations

import json
import re
from typing import Any


def parse_json_object(text: str) -> dict[str, Any]:
    """Parse a JSON object from model output (raw or fenced)."""
    raw = (text or "").strip()
    if not raw:
        raise ValueError("empty model response")
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw, re.IGNORECASE)
    if fence:
        raw = fence.group(1).strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no JSON object in model response")
    parsed = json.loads(raw[start : end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("model JSON must be an object")
    return parsed
