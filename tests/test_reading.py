"""Unit tests for reading item automation and dispatch."""

from unittest.mock import MagicMock, patch

from coursera_automation.config import Settings
from coursera_automation.items.content.reading import handle_reading
from coursera_automation.items.dispatcher import dispatch_item


def test_handle_reading_click_mark_complete() -> None:
    """Verify handle_reading clicks Mark as completed when active."""
    page, cfg = MagicMock(), Settings()
    btn = MagicMock()
    btn.is_visible.return_value = True
    btn.inner_text.return_value = "Mark as completed"
    page.locator.return_value.or_.return_value.first = btn

    with patch("coursera_automation.items.content.reading.dismiss_dialogs"):
        handle_reading(page, cfg)

    btn.scroll_into_view_if_needed.assert_called_once()
    btn.click.assert_called_once_with(force=True)
    assert page.mouse.wheel.call_count == 12


def test_handle_reading_already_completed() -> None:
    """Verify handle_reading skips clicking when reading item is already completed."""
    page, cfg = MagicMock(), Settings()
    btn = MagicMock()
    btn.is_visible.return_value = True
    btn.inner_text.return_value = "Completed"
    page.locator.return_value.or_.return_value.first = btn

    with patch("coursera_automation.items.content.reading.dismiss_dialogs"):
        handle_reading(page, cfg)

    btn.click.assert_not_called()


def test_dispatch_item_reading_supplement_url() -> None:
    """Verify dispatch_item detects reading via /supplement in URL."""
    page, cfg = MagicMock(), Settings()
    page.url = "https://www.coursera.org/learn/example/supplement/abc"
    page.locator.return_value.first.is_visible.return_value = False
    page.locator.return_value.filter.return_value.first.is_visible.return_value = False

    with (
        patch("coursera_automation.items.dispatcher.dismiss_dialogs"),
        patch("coursera_automation.items.dispatcher.handle_reading") as mock_read,
    ):
        dispatch_item(page, cfg)
        mock_read.assert_called_once_with(page, cfg)
