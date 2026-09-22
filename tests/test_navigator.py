"""Unit tests for navigator controls: click_resume and click_next_item."""

from unittest.mock import MagicMock, patch

from coursera_automation.config import Settings
from coursera_automation.items.navigation.navigator import click_next_item, click_resume


def test_click_resume_when_resume_present() -> None:
    """Verify click_resume prioritizes Resume button when visible."""
    page, cfg, res_btn, start_btn = MagicMock(), Settings(), MagicMock(is_visible=lambda: True), MagicMock(is_visible=lambda: True)
    page.locator.return_value.filter.side_effect = lambda **kw: MagicMock(first=start_btn) if "get started" in str(kw.get("has_text", "")).lower() else MagicMock(first=res_btn)
    with patch("coursera_automation.items.navigation.navigator.dismiss_dialogs"):
        click_resume(page, cfg)
    res_btn.click.assert_called_once_with(force=True)
    start_btn.click.assert_not_called()


def test_click_resume_fallback_get_started() -> None:
    """Verify click_resume falls back to Get started when Resume button is absent."""
    page, cfg, res_btn, start_btn = MagicMock(), Settings(), MagicMock(is_visible=lambda: False), MagicMock(is_visible=lambda: True)
    page.locator.return_value.filter.side_effect = lambda **kw: MagicMock(first=start_btn) if "get started" in str(kw.get("has_text", "")).lower() else MagicMock(first=res_btn)
    with patch("coursera_automation.items.navigation.navigator.dismiss_dialogs"):
        click_resume(page, cfg)
    res_btn.click.assert_not_called()
    start_btn.click.assert_called_once_with(force=True)


def test_click_next_item_advances() -> None:
    """Verify click_next_item locates progression button and navigates href if url unchanged."""
    page, cfg, btn = MagicMock(url="https://www.coursera.org/learn/quiz"), Settings(), MagicMock()
    page.goto.side_effect = lambda url, **kw: setattr(page, "url", url)
    btn.is_visible.return_value = True
    btn.get_attribute.return_value = "/learn/next"
    page.locator.side_effect = lambda s: MagicMock(first=MagicMock(is_visible=lambda *a, **kw: False)) if "Reviewing" in s else MagicMock(all=lambda: [btn])
    with patch("coursera_automation.items.navigation.navigator.dismiss_dialogs"):
        assert click_next_item(page, cfg) is True
    btn.click.assert_called_once()
    page.goto.assert_called_once_with("https://www.coursera.org/learn/next", wait_until="domcontentloaded")


def test_click_next_item_false_when_unchanged() -> None:
    """Verify click_next_item returns False when page URL does not advance."""
    page, cfg = MagicMock(url="https://coursera.org/quiz"), Settings()
    page.locator.return_value.all.return_value = []
    page.locator.return_value.first.is_visible.return_value = False
    with patch("coursera_automation.items.navigation.navigator.dismiss_dialogs"):
        assert click_next_item(page, cfg) is False


def test_click_resume_skips_on_item_page() -> None:
    """Verify click_resume skips button click when already on an item page."""
    page, cfg = MagicMock(url="https://coursera.org/learn/test/lecture/123"), Settings()
    with patch("coursera_automation.items.navigation.navigator.dismiss_dialogs") as mock_d:
        click_resume(page, cfg)
    mock_d.assert_not_called()
