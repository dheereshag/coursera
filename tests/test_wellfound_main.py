"""Tests for Wellfound entrypoint and runner."""

from unittest.mock import MagicMock, patch

import wellfound_main
from wellfound_automation.config import WellfoundConfig
from wellfound_automation.main import run


def test_run_orchestration() -> None:
    """Verify that run() launches context and executes login_wellfound."""
    mock_ctx = MagicMock()
    mock_page = MagicMock()
    mock_ctx.pages = [mock_page]

    with (
        patch("wellfound_automation.main.launch_wellfound_context") as mock_launch,
        patch("wellfound_automation.main.login_wellfound") as mock_login,
    ):
        mock_launch.return_value.__enter__.return_value = mock_ctx
        mock_login.return_value = True

        cfg = WellfoundConfig()
        result = run(cfg)

        assert result is True
        mock_login.assert_called_once_with(mock_page, cfg)


def test_wellfound_main_delegates() -> None:
    """Verify that wellfound_main.main calls wellfound_automation.main.run."""
    with patch("wellfound_main.run") as mock_run:
        wellfound_main.main()
        mock_run.assert_called_once()
