"""Tests for coursera_automation configuration."""

from coursera_automation.config import Settings, config


def test_default_config() -> None:
    """Verify default configuration values."""
    assert config.email == "24bai70310@cuchd.in"
    assert config.password == "Lakshya.24AI"
    assert "coursera.org" in config.login_url
    assert "generative-ai" in config.course_url
    assert config.post_quiz_wait_sec == 300


def test_custom_settings() -> None:
    """Verify custom settings overrides."""
    custom = Settings(email="custom@example.com", password="secret", timeout_ms=5000)
    assert custom.email == "custom@example.com"
    assert custom.password == "secret"
    assert custom.timeout_ms == 5000
