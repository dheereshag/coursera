"""Tests for Wellfound browser context management."""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from wellfound_automation.browser import (
    launch_wellfound_context,
    prepare_user_data_dir,
)
from wellfound_automation.config import WellfoundConfig


def test_prepare_user_data_dir_clears_locks() -> None:
    """Ensure directory is created and Singleton lock files are deleted."""
    with TemporaryDirectory() as tmp_dir:
        lock_file = Path(tmp_dir) / "SingletonLock"
        lock_file.write_text("lock")
        assert lock_file.exists()

        prepared = prepare_user_data_dir(tmp_dir)
        assert prepared == tmp_dir
        assert not lock_file.exists()


def test_launch_wellfound_context() -> None:
    """Ensure persistent context is launched with stealth."""
    with TemporaryDirectory() as tmp_dir:
        cfg = WellfoundConfig(user_data_dir=tmp_dir, headless=True)
        with (
            patch("wellfound_automation.browser.sync_playwright") as mock_pw,
            patch("wellfound_automation.browser.Stealth") as mock_stealth,
        ):
            mock_playwright_ctx = MagicMock()
            mock_pw.return_value.__enter__.return_value = mock_playwright_ctx
            mock_context = MagicMock()
            mock_playwright_ctx.chromium.launch_persistent_context.return_value = mock_context

            with launch_wellfound_context(cfg) as ctx:
                assert ctx is mock_context

            mock_stealth.return_value.apply_stealth_sync.assert_called_once_with(mock_context)
            mock_context.close.assert_called_once()
