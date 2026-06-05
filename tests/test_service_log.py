import logging

from app.service_log import (
    configure_logging,
    log_startup_from_issues,
    quiet_noisy_http_loggers,
    resolve_log_level,
    should_log_info,
)


def test_resolve_log_level_defaults_to_warn():
    assert resolve_log_level({}) == "warn"


def test_should_log_info_respects_level():
    assert should_log_info({"LOG_LEVEL": "warn"}) is False
    assert should_log_info({"LOG_LEVEL": "info"}) is True


def test_quiet_noisy_http_loggers_sets_httpx_to_warning():
    quiet_noisy_http_loggers()
    assert logging.getLogger("httpx").level >= logging.WARNING


def test_configure_logging_quiets_httpx():
    configure_logging("test-quiet-httpx")
    assert logging.getLogger("httpcore").level >= logging.WARNING


def test_log_startup_from_issues_warns_without_info_dump(caplog):
    import logging

    logger = logging.getLogger("test-service-log")
    config = {"service": "ai-orchestration", "llm_mode": "live", "groq_configured": False}
    issues = ["AI_LLM_MODE=live but GROQ_API_KEY is missing"]

    with caplog.at_level(logging.WARNING):
        log_startup_from_issues(logger, config, issues, {"LOG_LEVEL": "warn"})

    assert any("config issues" in record.message for record in caplog.records)
    assert not any("config {" in record.message for record in caplog.records)
