"""Tests for coursera_automation configuration."""

from coursera_automation.config import Settings, config


def test_default_config() -> None:
    """Verify default configuration values."""
    assert config.email == ""
    assert config.password == ""
    assert config.login_url == "https://www.coursera.org"
    assert config.headless is False
    assert config.openrouter_base_url == "https://openrouter.ai/api/v1"
    assert config.openrouter_model == "dots-studio/dots-3-note-preview:free"
    assert config.openrouter_vision_model == "nex-agi/nex-n2.5-mini:free"
    assert config.groq_model == "qwen/qwen3.8-27b"
    assert config.groq_vision_model == "qwen/qwen3.8-27b"
    assert config.post_quiz_wait_sec == 180


def test_custom_settings() -> None:
    """Verify custom settings overrides."""
    custom = Settings(email="custom@example.com", password="secret", timeout_ms=5000)
    assert custom.email == "custom@example.com"
    assert custom.password == "secret"
    assert custom.timeout_ms == 5000
