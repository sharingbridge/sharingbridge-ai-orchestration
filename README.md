# sharingbridge-ai-orchestration

> Internal LLM orchestration for donor setup suggestions and donor–seeker instruction packs.

## Overview

This service exposes **internal** HTTP routes called by `sharingbridge-integration-service`. Mobile apps never call it directly.

**MVP behavior:** `AI_LLM_MODE=passthrough` (default) echoes the user's search text / assembles instruction text from request fields — **no invented vendor catalog**. Hardcoded sample restaurants exist only in unit-test fixtures.

**Live LLM:** `AI_LLM_MODE=live` with **Gemini** (reference-photo vision) and **Groq** (text). See [ai-setup-handhold.md](https://github.com/sharingbridge/sharingbridge/blob/main/configuration/ai-setup-handhold.md).

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | Liveness |
| `POST` | `/internal/v1/llm/suggest-vendors` | Top vendor/menu suggestions |
| `POST` | `/internal/v1/llm/instruction-pack` | Delivery instruction narrative |

Protect internal routes with `X-Internal-Api-Key` when `AI_ORCHESTRATION_INTERNAL_API_KEY` is set (static service key, not a user JWT).

## Run locally

Requires **Python 3.10+** (3.13 works for local dev). Docker image uses Python 3.12. Use `python3.13` — not Anaconda’s default `python` (often 3.7).

**Use a project virtualenv on Windows** — create `.venv` **in this repo only** (not `D:\kannan\sharingbridge\.venv`). Do not `pip install` into Anaconda’s global `ProgramData` folder (you may see `WinError 5 Access is denied` when upgrading `pytest`).

**Uvicorn** is the Python HTTP server for this app (like `npm start` for Node). **`Activate.ps1`** is generated under `.venv\Scripts\` when you run `python3.13 -m venv .venv`; it is gitignored. See [ai-orchestration-local.md](https://github.com/sharingbridge/sharingbridge/blob/main/configuration/ai-orchestration-local.md).

```powershell
cd D:\kannan\sharingbridge\sharingbridge-ai-orchestration

python3.13 -m venv .venv
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
| `AI_ORCHESTRATION_INTERNAL_API_KEY` | Static API key shared with integration-service |
| `AI_LLM_MODE` | `passthrough` (default) or `live` (`deterministic` = legacy alias of passthrough) |
| `GROQ_API_KEY` / `GROQ_MODEL` | Text: suggest-vendors + instruction compose |
| `GEMINI_API_KEY` / `GEMINI_VISION_MODEL` | Vision: reference photo (`gemini-2.5-flash`) |
| `NOMINATIM_USER_AGENT` | Reverse geocode User-Agent (no API key) |
| `SHARINGBRIDGE_WEBSITE_URL` | Courier instruction text only (not an API URL). Use `pending` until you have a real site, then `https://…`. |

Copy `env.example` to `.env` for local overrides.

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
| `uvicorn` not found | Venv not activated or wrong folder | `cd` this repo, `.\.venv\Scripts\Activate.ps1`, or `.\.venv\Scripts\python.exe -m uvicorn ...` |
| Empty `Activate.ps1` | Broken venv (often created in parent folder) | Delete `.venv` here, run `python3.13 -m venv .venv` again in **this** repo |
| `ForwardRef._evaluate() … recursive_guard` on `uvicorn` | Pydantic v1 + Python 3.13 | `git pull`, delete `.venv`, `python3.13 -m venv .venv`, `pip install -r requirements.txt` |

## Deploy (Render)

- **Docker** web service (`Dockerfile` + `start.sh`).
- **Leave Start Command blank** on Render (use the image CMD only).
- Set `AI_ORCHESTRATION_INTERNAL_API_KEY` to match integration-service.
- Set `SHARINGBRIDGE_WEBSITE_URL=pending` until you have a real public site.
- [configuration/backend-render.md](https://github.com/sharingbridge/sharingbridge/blob/main/configuration/backend-render.md)

## Coordination docs

- [AI_AS_BUILT.md](https://github.com/sharingbridge/sharingbridge/blob/main/development/AI_AS_BUILT.md)
- [AI_PLAN.md](https://github.com/sharingbridge/sharingbridge/blob/main/development/AI_PLAN.md)
- [STATUS.md](https://github.com/sharingbridge/sharingbridge/blob/main/development/STATUS.md)
