from fastapi import Depends, FastAPI

from .auth import require_internal_token
from .schemas import (
    InstructionPackRequest,
    InstructionPackResponse,
    SuggestVendorsRequest,
    SuggestVendorsResponse,
)
from .services.instruction_pack import build_instruction_pack_response
from .services.suggest_vendors import build_suggest_vendors_response

app = FastAPI(
    title="SharingBridge AI Orchestration",
    version="0.1.0",
    description="Internal LLM orchestration for suggest-vendors and instruction-pack.",
)


@app.get("/health")
def health() -> dict:
    return {"ok": True, "service": "ai-orchestration"}


@app.post(
    "/internal/v1/llm/suggest-vendors",
    response_model=SuggestVendorsResponse,
    dependencies=[Depends(require_internal_token)],
)
def suggest_vendors(body: SuggestVendorsRequest) -> dict:
    return build_suggest_vendors_response(body.dict())


@app.post(
    "/internal/v1/llm/instruction-pack",
    response_model=InstructionPackResponse,
    dependencies=[Depends(require_internal_token)],
)
def instruction_pack(body: InstructionPackRequest) -> dict:
    payload = body.dict()
    payload["presets"] = [p.dict() for p in body.presets]
    return build_instruction_pack_response(payload)
