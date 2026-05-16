from typing import Optional

from fastapi import Header, HTTPException

from .config import settings


def require_internal_api_key(
    x_internal_api_key: Optional[str] = Header(None, alias="X-Internal-Api-Key"),
):
    expected = settings.internal_api_key
    if not expected:
        return
    if not x_internal_api_key or x_internal_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid internal API key")
