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

**Use a project virtualenv on Windows** — do not `pip install` into Anaconda’s global `ProgramData` folder (you may see `WinError 5 Access is denied` when upgrading `pytest`). The API server only needs `fastapi` + `uvicorn`; those errors during `pytest` install do not block `uvicorn` if they are already present.

```powershell
cd D:\kannan\sharingbridge\sharingbridge-ai-orchestration

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

$env:PORT = "8091"
uvicorn app.main:app --host 0.0.0.0 --port 8091
```

Verify (second terminal):

```powershell
Invoke-RestMethod http://127.0.0.1:8091/health
# Expect: ok=True, service=ai-orchestration
```

Leave that window open while integration-service runs with `AI_ORCHESTRATION_BASE_URL=http://localhost:8091`.

## Environment

| Variable | Description |
|----------|-------------|
| `PORT` | Listen port (default `8091`) |
| `AI_ORCHESTRATION_INTERNAL_TOKEN` | Shared secret with integration-service |
| `AI_LLM_MODE` | `deterministic` (default) or `openai` (future) |
| `OPENAI_API_KEY` | Required only when using OpenAI mode |
| `SHARINGBRIDGE_WEBSITE_URL` | Courier instruction text only (not an API URL). Use `pending` until you have a real site, then `https://…`. |

## Tests

With the venv activated:

```powershell
python -m pytest -q
```

## Troubleshooting (Windows)

| Symptom | Cause | Fix |
|---------|--------|-----|
| `WinError 5` / `Access is denied` on `pip install` | Installing into system Anaconda without admin | Use `.venv` steps above |
| `pytest-astropy requires pytest-cov` | Unrelated global Anaconda plugin | Ignore if you only run the server; use venv for tests |
| Red pip errors but `Uvicorn running on http://0.0.0.0:8091` | `fastapi`/`uvicorn` already installed globally | **Server is fine** — open `http://127.0.0.1:8091/health` |
| `uvicorn` not found | Venv not activated | `.\.venv\Scripts\Activate.ps1` then retry |

## Deploy (Render)

- **Docker** web service (`Dockerfile` + `start.sh`).
- **Leave Start Command blank** on Render (use the image CMD only).
- Set `AI_ORCHESTRATION_INTERNAL_TOKEN` to match integration-service.
- Set `SHARINGBRIDGE_WEBSITE_URL=pending` until you have a real public site.
- Guide: [DEPLOY_RENDER.md](https://github.com/sharingbridge/sharingbridge/blob/main/development/DEPLOY_RENDER.md).

## Coordination docs

- [AI_PLATFORM_INTEGRATION.md](https://github.com/sharingbridge/sharingbridge/blob/main/development/AI_PLATFORM_INTEGRATION.md)
- [IMPLEMENTATION_APPROACH.md](https://github.com/sharingbridge/sharingbridge/blob/main/development/IMPLEMENTATION_APPROACH.md)
