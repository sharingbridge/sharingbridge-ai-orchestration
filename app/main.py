import os
import time
import uuid

from fastapi import Depends, FastAPI

from .auth import require_internal_api_key
from .config import settings
from .schemas import (
    InstructionPackRequest,
    InstructionPackResponse,
    SuggestVendorsRequest,
    SuggestVendorsResponse,
)
from .service_log import (
    configure_logging,
    log_info,
    log_startup_from_issues,
    resolve_log_level,
)
from .services.instruction_pack import build_instruction_pack_response
from .services.suggest_vendors import build_suggest_vendors_response

app = FastAPI(
    title="SharingBridge AI Orchestration",
    version="0.1.0",
    description="Internal LLM orchestration for suggest-vendors and instruction-pack.",
)

logger = configure_logging("ai-orchestration")


def _public_config() -> dict:
    return {
        "service": "ai-orchestration",
        "llm_mode": settings.llm_mode,
        "live_llm_enabled": settings.live_llm_enabled(),
        "groq_configured": settings.groq_configured(),
        "gemini_configured": settings.gemini_configured(),
        "groq_model": settings.groq_model,
        "gemini_vision_model": settings.gemini_vision_model,
        "photo_service_base_url_set": bool(settings.photo_service_base_url),
        "internal_api_key_required": bool(settings.internal_api_key),
        "nominatim_user_agent_set": bool(
            os.getenv("NOMINATIM_USER_AGENT", "").strip()
        ),
        "log_level": resolve_log_level(),
    }


def _startup_config_issues(config: dict) -> list[str]:
    issues: list[str] = []
    if config.get("llm_mode") == "live" and not config.get("groq_configured"):
        issues.append("AI_LLM_MODE=live but GROQ_API_KEY is missing")
    if config.get("llm_mode") == "live" and not config.get("gemini_configured"):
        issues.append("AI_LLM_MODE=live but GEMINI_API_KEY is missing")
    vision_model = str(config.get("gemini_vision_model") or "")
    if vision_model.startswith("gemini-2.0-flash"):
        issues.append(
            "GEMINI_VISION_MODEL is shut down (June 2026); "
            "set gemini-2.5-flash or gemini-3.5-flash"
        )
    return issues


@app.on_event("startup")
def log_startup_config() -> None:
    config = _public_config()
    log_startup_from_issues(logger, config, _startup_config_issues(config))


@app.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "service": "ai-orchestration",
        "config": _public_config(),
    }


@app.post(
    "/internal/v1/llm/suggest-vendors",
    response_model=SuggestVendorsResponse,
    dependencies=[Depends(require_internal_api_key)],
)
def suggest_vendors(body: SuggestVendorsRequest) -> dict:
    return build_suggest_vendors_response(body.model_dump())


@app.post(
    "/internal/v1/llm/instruction-pack",
    response_model=InstructionPackResponse,
    dependencies=[Depends(require_internal_api_key)],
)
def instruction_pack(body: InstructionPackRequest) -> dict:
    request_id = uuid.uuid4().hex[:8]
    started = time.perf_counter()
    log_info(
        logger,
        "[instruction-pack] %s start has_photo=%s",
        request_id,
        body.has_reference_photo,
    )
    payload = body.model_dump()
    payload["presets"] = [p.model_dump() for p in body.presets]
    result = build_instruction_pack_response(payload)
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    log_info(
        logger,
        "[instruction-pack] %s done in %dms source=%s",
        request_id,
        elapsed_ms,
        result.get("source"),
    )
    return result
