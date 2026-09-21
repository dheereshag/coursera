"""Unit tests for lab handling: agreement check, progressive scroll, and launch."""

from unittest.mock import MagicMock, patch

from coursera_automation.config import Settings
from coursera_automation.items.lab import _check_agreement, handle_lab


def test_check_agreement_uncheck() -> None:
    """Verify _check_agreement checks the checkbox when visible and unchecked."""
    page = MagicMock()
    agree_box = MagicMock(is_visible=MagicMock(return_value=True), is_checked=MagicMock(return_value=False))
    page.get_by_label.return_value.or_.return_value.first = agree_box
    _check_agreement(page)
    agree_box.check.assert_called_once_with(force=True)


def test_handle_lab_progressive_scroll() -> None:
    """Verify handle_lab scrolls progressively and clicks Launch button."""
    page, cfg = MagicMock(), Settings()
    launch_btn = MagicMock(is_visible=MagicMock(side_effect=[False, False, True, True]))
    page.locator.return_value.filter.return_value.first = launch_btn

    with (
        patch("coursera_automation.items.lab._check_agreement") as mock_agree,
        patch("coursera_automation.items.lab.dismiss_dialogs"),
    ):
        handle_lab(page, cfg)
        assert mock_agree.call_count >= 3
        launch_btn.click.assert_called_once_with(force=True)
        assert page.mouse.wheel.call_count == 2


def test_handle_lab_bottom_fallback() -> None:
    """Verify handle_lab executes window scrollTo bottom fallback if needed."""
    page, cfg = MagicMock(), Settings()
    launch_btn = MagicMock(is_visible=MagicMock(return_value=False))
    page.locator.return_value.filter.return_value.first = launch_btn

    with (
        patch("coursera_automation.items.lab._check_agreement"),
        patch("coursera_automation.items.lab.dismiss_dialogs"),
    ):
        handle_lab(page, cfg)
        page.evaluate.assert_called_with("() => window.scrollTo(0, document.body.scrollHeight)")
