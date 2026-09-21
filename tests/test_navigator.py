"""Unit tests for navigator controls: click_resume and click_next_item."""

from unittest.mock import MagicMock, patch

from coursera_automation.config import Settings
from coursera_automation.items.navigation.navigator import click_next_item, click_resume


def test_click_resume_when_resume_present() -> None:
    """Verify click_resume prioritizes Resume button when visible."""
    page, cfg = MagicMock(), Settings()
    res_btn, start_btn = MagicMock(is_visible=MagicMock(return_value=True)), MagicMock(is_visible=MagicMock(return_value=True))
    res_loc, start_loc = MagicMock(first=res_btn), MagicMock(first=start_btn)

    def mock_filter(**kw):
        return start_loc if "has_text" in kw and "get started" in str(kw["has_text"]).lower() else res_loc

    page.locator.return_value.filter.side_effect = mock_filter
    with patch("coursera_automation.items.navigation.navigator.dismiss_dialogs"):
        click_resume(page, cfg)
    res_btn.click.assert_called_once_with(force=True)
    page.wait_for_timeout.assert_any_call(10000)
    start_btn.click.assert_not_called()


def test_click_resume_fallback_get_started() -> None:
    """Verify click_resume falls back to Get started when Resume button is absent."""
    page, cfg = MagicMock(), Settings()
    res_btn, start_btn = MagicMock(is_visible=MagicMock(return_value=False)), MagicMock(is_visible=MagicMock(return_value=True))
    res_loc, start_loc = MagicMock(first=res_btn), MagicMock(first=start_btn)

    def mock_filter(**kw):
        return start_loc if "has_text" in kw and "get started" in str(kw["has_text"]).lower() else res_loc

    page.locator.return_value.filter.side_effect = mock_filter
    with patch("coursera_automation.items.navigation.navigator.dismiss_dialogs"):
        click_resume(page, cfg)
    res_btn.click.assert_not_called()
    start_btn.click.assert_called_once_with(force=True)


def test_click_next_item_advances() -> None:
    """Verify click_next_item locates progression button and navigates href if url unchanged."""
    page, cfg, btn = MagicMock(), Settings(), MagicMock()
    page.url = "https://www.coursera.org/learn/quiz"
    btn.first.is_visible.return_value = True
    btn.first.get_attribute.return_value = "/learn/next"
    page.locator.side_effect = lambda s: MagicMock(first=MagicMock(is_visible=MagicMock(return_value=False))) if "Reviewing" in s else btn
    with patch("coursera_automation.items.navigation.navigator.dismiss_dialogs"):
        assert click_next_item(page, cfg) is True
    btn.first.click.assert_called_once()
    page.goto.assert_called_once_with("https://www.coursera.org/learn/next", wait_until="domcontentloaded")
