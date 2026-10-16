"""Tests for Wellfound configuration."""

import os
from unittest.mock import patch

from wellfound_automation.config import WellfoundConfig


def test_default_wellfound_config() -> None:
    """Verify default credentials and endpoints for Wellfound."""
    with patch.dict(os.environ, {}, clear=True):
        cfg = WellfoundConfig()
        assert cfg.email == "da11@iitbbs.ac.in"
        assert cfg.password == "Derek_20173017"
        assert cfg.base_url == "https://wellfound.com"
        assert cfg.login_url == "https://wellfound.com/login"
        assert cfg.user_data_dir == ".browser_data/wellfound"
        assert cfg.headless is False
        assert cfg.timeout_ms == 15000


def test_custom_wellfound_config_overrides() -> None:
    """Verify environment variable overrides for Wellfound config."""
    env = {
        "WELLFOUND_EMAIL": "custom@domain.com",
        "WELLFOUND_PASSWORD": "secret_password",
        "WELLFOUND_BASE_URL": "https://custom.wellfound.com",
        "WELLFOUND_LOGIN_URL": "https://custom.wellfound.com/login",
        "WELLFOUND_USER_DATA_DIR": "/tmp/wellfound",
        "WELLFOUND_HEADLESS": "true",
    }
    with patch.dict(os.environ, env, clear=True):
        cfg = WellfoundConfig()
        assert cfg.email == "custom@domain.com"
        assert cfg.password == "secret_password"
        assert cfg.base_url == "https://custom.wellfound.com"
        assert cfg.login_url == "https://custom.wellfound.com/login"
        assert cfg.user_data_dir == "/tmp/wellfound"
        assert cfg.headless is True
