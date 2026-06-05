from app.main import _startup_config_issues


def test_startup_warns_on_shutdown_gemini_vision_model():
    config = {
        "llm_mode": "live",
        "groq_configured": True,
        "gemini_configured": True,
        "gemini_vision_model": "gemini-2.0-flash",
    }
    issues = _startup_config_issues(config)
    assert any("shut down" in issue for issue in issues)


def test_startup_ok_for_current_gemini_vision_model():
    config = {
        "llm_mode": "live",
        "groq_configured": True,
        "gemini_configured": True,
        "gemini_vision_model": "gemini-2.5-flash",
    }
    assert _startup_config_issues(config) == []
