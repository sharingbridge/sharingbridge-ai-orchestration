import os


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    def __init__(self) -> None:
        self.internal_api_key = os.getenv(
            "AI_ORCHESTRATION_INTERNAL_API_KEY", ""
        ).strip()
        self.llm_mode = os.getenv("AI_LLM_MODE", "passthrough").strip().lower()
        # Non-live modes: passthrough (echo/assemble user input). Legacy alias: deterministic.
        # Groq — text: presets + instruction compose
        self.groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.groq_model = os.getenv(
            "GROQ_MODEL", "llama-3.3-70b-versatile"
        ).strip()
        self.groq_base_url = os.getenv(
            "GROQ_BASE_URL", "https://api.groq.com/openai/v1"
        ).strip().rstrip("/")
        # Gemini — vision: image + seeker appearance hints
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.gemini_vision_model = os.getenv(
            "GEMINI_VISION_MODEL", "gemini-2.5-flash"
        ).strip()
        self.photo_service_base_url = os.getenv(
            "PHOTO_SERVICE_BASE_URL", ""
        ).strip().rstrip("/")
        # Courier instruction text only — use "pending" until a real https URL exists.
        self.website_url = os.getenv("SHARINGBRIDGE_WEBSITE_URL", "pending").strip()

    def live_llm_enabled(self) -> bool:
        return self.llm_mode == "live"

    def groq_configured(self) -> bool:
        return bool(self.groq_api_key)

    def gemini_configured(self) -> bool:
        return bool(self.gemini_api_key)


settings = Settings()
