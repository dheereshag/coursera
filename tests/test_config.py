"""Tests for coursera_automation configuration."""

from coursera_automation.config import Settings, config


def test_default_config() -> None:
    """Verify default global configuration values."""
    assert config.login_url == "https://www.coursera.org"
    assert config.openrouter_base_url == "https://openrouter.ai/api/v1"
    assert config.openrouter_model == "deepseek/deepseek-v4.1-flash"
    assert config.openrouter_fallback_model == "z-ai/glm-5.3-flash"
    assert config.post_quiz_wait_sec == 180


def test_custom_settings() -> None:
    """Verify custom settings overrides."""
    custom = Settings(timeout_ms=5000, post_quiz_wait_sec=90)
    assert custom.timeout_ms == 5000
    assert custom.post_quiz_wait_sec == 90


def test_session_config() -> None:
    """Verify SessionConfig bundles instance credentials with Settings."""
    from coursera_automation.session import SessionConfig

    session = SessionConfig(
        email="test@example.com",
        password="pwd",
        course_url="https://coursera.org/test",
        legal_name="Test User",
        headless=True,
    )
    assert isinstance(session, Settings)
    assert session.email == "test@example.com"
    assert session.password == "pwd"
    assert session.course_url == "https://coursera.org/test"
    assert session.legal_name == "Test User"
    assert session.headless is True
