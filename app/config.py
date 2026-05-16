import os


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    def __init__(self) -> None:
        self.internal_token = os.getenv("AI_ORCHESTRATION_INTERNAL_TOKEN", "").strip()
        self.llm_mode = os.getenv("AI_LLM_MODE", "deterministic").strip().lower()
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.openai_model = os.getenv("AI_LLM_MODEL", "gpt-4o-mini").strip()
        # Courier instruction text only — use "pending" until a real https URL exists.
        self.website_url = os.getenv("SHARINGBRIDGE_WEBSITE_URL", "pending").strip()


settings = Settings()
