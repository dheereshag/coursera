"""Unit tests for discussion prompt automation."""

from unittest.mock import MagicMock

from coursera_automation.config import Settings
from coursera_automation.items.interactive.discussion import handle_discussion


def test_handle_discussion_fills_and_submits() -> None:
    """Verify handle_discussion fills chatbox, clicks Reply, and waits 10s."""
    page, cfg = MagicMock(), Settings()
    chatbox = MagicMock(is_visible=MagicMock(return_value=True))
    reply_btn = MagicMock(is_visible=MagicMock(return_value=True))

    page.locator.return_value.first = chatbox
    page.get_by_role.return_value.or_.return_value.first = reply_btn

    handle_discussion(page, cfg)

    chatbox.fill.assert_called_once_with("ok")
    reply_btn.click.assert_called_once()
    page.wait_for_timeout.assert_any_call(15000)


def test_handle_discussion_bypasses_when_absent() -> None:
    """Verify handle_discussion exits gracefully when chatbox is absent."""
    page, cfg = MagicMock(), Settings()
    page.locator.return_value.first.is_visible.return_value = False
    handle_discussion(page, cfg)
    page.get_by_role.assert_not_called()
