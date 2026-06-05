from __future__ import annotations

import json
import logging
import os
from typing import Any

LEVEL_RANK = {
    "error": logging.ERROR,
    "warn": logging.WARNING,
    "warning": logging.WARNING,
    "info": logging.INFO,
    "debug": logging.DEBUG,
}

VERBOSITY_RANK = {
    "error": 0,
    "warn": 1,
    "info": 2,
    "debug": 3,
}


def resolve_log_level(env: dict[str, str] | None = None) -> str:
    source = env if env is not None else os.environ
    raw = str(source.get("LOG_LEVEL", "warn")).strip().lower()
    if raw == "warning":
        raw = "warn"
    return raw if raw in LEVEL_RANK else "warn"


def quiet_noisy_http_loggers() -> None:
    """Keep httpx/httpcore from logging full URLs (Gemini keys in query strings)."""
    for name in ("httpx", "httpcore", "urllib3"):
        logging.getLogger(name).setLevel(logging.WARNING)


def configure_logging(logger_name: str = "sharingbridge") -> logging.Logger:
    level_name = resolve_log_level()
    logging.basicConfig(
        level=LEVEL_RANK[level_name],
        format="%(message)s",
        force=True,
    )
    quiet_noisy_http_loggers()
    return logging.getLogger(logger_name)


def log_info(logger: logging.Logger, message: str, *args: Any) -> None:
    if should_log_info():
        logger.info(message, *args)


def should_log_info(env: dict[str, str] | None = None) -> bool:
    level = resolve_log_level(env)
    return VERBOSITY_RANK[level] >= VERBOSITY_RANK["info"]


def log_startup_from_issues(
    logger: logging.Logger,
    config: dict[str, Any],
    issues: list[str],
    env: dict[str, str] | None = None,
) -> None:
    if issues:
        logger.warning("[startup] config issues: %s", json.dumps(issues))
    elif should_log_info(env):
        logger.info("[startup] config %s", json.dumps(config))


def log_warn(logger: logging.Logger, message: str, *args: Any) -> None:
    logger.warning(message, *args)
