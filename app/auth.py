from typing import Optional

from fastapi import Header, HTTPException

from .config import settings


def require_internal_token(
    x_internal_token: Optional[str] = Header(None, alias="X-Internal-Token"),
):
    expected = settings.internal_token
    if not expected:
        return
    if not x_internal_token or x_internal_token != expected:
        raise HTTPException(status_code=401, detail="Invalid internal token")
