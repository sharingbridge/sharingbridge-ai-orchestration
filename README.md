# sharingbridge-ai-orchestration

> Internal LLM orchestration for donor setup suggestions and donor–seeker instruction packs.

## Overview

This service exposes **internal** HTTP routes called by `sharingbridge-integration-service`. Mobile apps never call it directly.

**MVP behavior:** `AI_LLM_MODE=deterministic` (default) returns query-ranked vendor suggestions and policy-aligned instruction packs without calling a model provider. Set `OPENAI_API_KEY` and `AI_LLM_MODE=openai` when you are ready to add a real LLM pass (LangChain wiring is planned; deterministic mode keeps CI free of live API keys).

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | Liveness |
| `POST` | `/internal/v1/llm/suggest-vendors` | Top vendor/menu suggestions |
| `POST` | `/internal/v1/llm/instruction-pack` | Delivery instruction narrative |

Protect internal routes with `X-Internal-Token` when `AI_ORCHESTRATION_INTERNAL_TOKEN` is set.

## Run locally

Requires **Python 3.7+** (3.10+ recommended for production deploy). Docker image uses Python 3.12.

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
set PORT=8091
uvicorn app.main:app --host 0.0.0.0 --port 8091
```

## Environment

| Variable | Description |
|----------|-------------|
| `PORT` | Listen port (default `8091`) |
| `AI_ORCHESTRATION_INTERNAL_TOKEN` | Shared secret with integration-service |
| `AI_LLM_MODE` | `deterministic` (default) or `openai` (future) |
| `OPENAI_API_KEY` | Required only when using OpenAI mode |
| `SHARINGBRIDGE_WEBSITE_URL` | Inserted into instruction-pack template |

## Tests

```bash
pytest
```

## Coordination docs

- [AI_PLATFORM_INTEGRATION.md](https://github.com/sharingbridge/sharingbridge/blob/main/development/AI_PLATFORM_INTEGRATION.md)
- [IMPLEMENTATION_APPROACH.md](https://github.com/sharingbridge/sharingbridge/blob/main/development/IMPLEMENTATION_APPROACH.md)
