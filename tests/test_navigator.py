"""Unit tests for navigator controls: click_resume and click_next_item."""

from unittest.mock import MagicMock, patch

from coursera_automation.config import Settings
from coursera_automation.items.navigator import click_next_item, click_resume


def test_click_resume_when_resume_present() -> None:
    """Verify click_resume prioritizes Resume button when visible."""
    page, cfg = MagicMock(), Settings()
    res_btn = MagicMock(is_visible=MagicMock(return_value=True))
    start_btn = MagicMock(is_visible=MagicMock(return_value=True))
    res_loc = MagicMock(first=res_btn)
    start_loc = MagicMock(first=start_btn)

    def mock_filter(**kw):
        if "has_text" in kw and "get started" in str(kw["has_text"]).lower():
            return start_loc
        return res_loc

    page.locator.return_value.filter.side_effect = mock_filter
    with patch("coursera_automation.items.navigator.dismiss_dialogs"):
        click_resume(page, cfg)
    res_btn.click.assert_called_once_with(force=True)
    start_btn.click.assert_not_called()


def test_click_resume_fallback_get_started() -> None:
    """Verify click_resume falls back to Get started when Resume button is absent."""
    page, cfg = MagicMock(), Settings()
    res_btn = MagicMock(is_visible=MagicMock(return_value=False))
    start_btn = MagicMock(is_visible=MagicMock(return_value=True))
    res_loc = MagicMock(first=res_btn)
    start_loc = MagicMock(first=start_btn)

    def mock_filter(**kw):
        if "has_text" in kw and "get started" in str(kw["has_text"]).lower():
            return start_loc
        return res_loc

    page.locator.return_value.filter.side_effect = mock_filter
    with patch("coursera_automation.items.navigator.dismiss_dialogs"):
        click_resume(page, cfg)
    res_btn.click.assert_not_called()
    start_btn.click.assert_called_once_with(force=True)


def test_click_next_item_advances() -> None:
    """Verify click_next_item locates progression button and clicks it."""
    page, cfg, btn = MagicMock(), Settings(), MagicMock()
    btn.first.is_visible.return_value = True
    page.locator.return_value = btn
    with patch("coursera_automation.items.navigator.dismiss_dialogs"):
        assert click_next_item(page, cfg) is True
    btn.first.click.assert_called_once_with(force=True)
