"""Unit tests for item calculation and logic."""

from unittest.mock import MagicMock, patch

from coursera_automation.config import Settings
from coursera_automation.items.dispatcher import dispatch_item
from coursera_automation.items.navigation import click_next_item, dismiss_dialogs


def test_dispatch_item_video() -> None:
    """Verify dispatch_item detects lecture URL and delegates to handle_video."""
    mock_page, cfg = MagicMock(), Settings()
    mock_page.url = "https://www.coursera.org/learn/example/lecture/abc"
    with (
        patch("coursera_automation.items.dispatcher.dismiss_dialogs"),
        patch("coursera_automation.items.dispatcher.handle_video") as mock_vid,
    ):
        dispatch_item(mock_page, cfg)
        mock_vid.assert_called_once_with(mock_page, cfg)
        mock_page.wait_for_timeout.assert_any_call(7000)


def test_dispatch_item_assignment() -> None:
    """Verify dispatch_item identifies assignment via .first and delegates to handle_quiz."""
    mock_page, cfg = MagicMock(), Settings()
    mock_page.url = "https://www.coursera.org/learn/example/exam/abc"
    mock_page.locator.side_effect = lambda s: MagicMock(
        first=MagicMock(is_visible=MagicMock(return_value="assignment" in s)),
        filter=MagicMock(return_value=MagicMock(first=MagicMock(is_visible=MagicMock(return_value=False)))),
    )
    with (
        patch("coursera_automation.items.dispatcher.dismiss_dialogs"),
        patch("coursera_automation.items.dispatcher.handle_quiz") as mock_quiz,
    ):
        dispatch_item(mock_page, cfg)
        mock_quiz.assert_called_once_with(mock_page, cfg)


def test_dismiss_dialogs_honor_code() -> None:
    """Verify dismiss_dialogs clicks Continue on HonorCodeModal."""
    page, honor = MagicMock(), MagicMock()
    honor.first.is_visible.return_value = True
    btn = honor.first.locator.return_value.first
    btn.is_visible.return_value = True
    page.locator.side_effect = lambda s: honor if "HonorCodeModal" in s else MagicMock(first=MagicMock(is_visible=lambda timeout=0: False))
    dismiss_dialogs(page)
    btn.click.assert_called_once_with(force=True)


def test_click_next_item_top_banner() -> None:
    """Verify click_next_item clicks TopBannerCTAButton when back button is visible."""
    page, cfg, btn = MagicMock(url="https://coursera.org/item1"), Settings(), MagicMock()
    btn.first.is_visible.return_value = True
    btn.first.click.side_effect = lambda **kw: setattr(page, "url", "https://coursera.org/item2")
    btn.click.side_effect = lambda **kw: setattr(page, "url", "https://coursera.org/item2")
    page.locator.side_effect = lambda s: btn if any(k in s for k in ("TopBannerCTAButton", "tunnel-vision-back-button", "Back")) else MagicMock(first=MagicMock(is_visible=lambda timeout=0: False))
    with patch("coursera_automation.items.navigation.navigator.dismiss_dialogs"):
        assert click_next_item(page, cfg) is True
    assert btn.click.called or btn.first.click.called


def test_click_next_item_without_back_button() -> None:
    """Verify click_next_item uses standard locators when back button is absent."""
    page, cfg, btn = MagicMock(url="https://coursera.org/item1"), Settings(), MagicMock()
    btn.first.is_visible.return_value = True
    btn.first.click.side_effect = lambda **kw: setattr(page, "url", "https://coursera.org/item2")
    btn.click.side_effect = lambda **kw: setattr(page, "url", "https://coursera.org/item2")
    btn.all.return_value = [btn]
    page.locator.side_effect = lambda s: btn if "next-item" in s else MagicMock(first=MagicMock(is_visible=lambda timeout=0: False), all=list)
    with patch("coursera_automation.items.navigation.navigator.dismiss_dialogs"):
        assert click_next_item(page, cfg) is True
    assert btn.click.called or btn.first.click.called


