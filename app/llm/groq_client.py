from __future__ import annotations

import json
import logging
import time
from typing import Any

import httpx

from ..config import settings
from ..service_log import log_info
from .json_utils import parse_json_object

logger = logging.getLogger("ai-orchestration")


class GroqClientError(Exception):
    pass


class GroqClient:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout_s: float = 45.0,
    ) -> None:
        self.api_key = (api_key or settings.groq_api_key).strip()
        self.base_url = (base_url or settings.groq_base_url).rstrip("/")
        self.model = (model or settings.groq_model).strip()
        self.timeout_s = timeout_s

    def configured(self) -> bool:
        return bool(self.api_key)

    def chat(
        self,
        *,
        system: str,
        user: str,
        json_mode: bool = False,
        temperature: float = 0.3,
    ) -> str:
        if not self.configured():
            raise GroqClientError("GROQ_API_KEY is not set")

        body: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
        }
        if json_mode:
            body["response_format"] = {"type": "json_object"}

        log_info(logger, "[groq] chat request model=%s json=%s", self.model, json_mode)
        response = None
        with httpx.Client(timeout=self.timeout_s) as client:
            for attempt in range(3):
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=body,
                )
                if response.status_code != 429 or attempt >= 2:
                    break
                time.sleep(2 * (attempt + 1))

        if response.status_code >= 400:
            raise GroqClientError(
                f"Groq HTTP {response.status_code}: {response.text[:500]}"
            )

        data = response.json()
        choices = data.get("choices") or []
        if not choices:
            raise GroqClientError("Groq returned no choices")
        message = choices[0].get("message") or {}
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise GroqClientError("Groq returned empty content")
        return content.strip()

    def chat_json(self, *, system: str, user: str, temperature: float = 0.3) -> dict[str, Any]:
        text = self.chat(
            system=system,
            user=user,
            json_mode=True,
            temperature=temperature,
        )
        try:
            return parse_json_object(text)
        except (ValueError, json.JSONDecodeError) as exc:
            raise GroqClientError(f"invalid JSON from Groq: {exc}") from exc
