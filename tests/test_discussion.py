"""Unit tests for discussion prompt automation."""

from unittest.mock import MagicMock

from coursera_automation.config import Settings
from coursera_automation.items.interactive.discussion import handle_discussion


def test_handle_discussion_fills_and_submits() -> None:
    """Verify handle_discussion clicks chatbox, types with press_sequentially, and dwells 60s."""
    page, cfg = MagicMock(), Settings()
    chatbox = MagicMock(is_visible=MagicMock(return_value=True))
    reply_btn = MagicMock(is_visible=MagicMock(return_value=True), is_enabled=MagicMock(return_value=True))
    reply_btn.get_attribute.return_value = "false"
    next_btn = MagicMock(is_visible=MagicMock(return_value=False))

    def loc_mock(s: str) -> MagicMock:
        if "next item" in s.lower():
            return MagicMock(first=next_btn)
        if "thread_reply" in s:
            return MagicMock(first=reply_btn)
        return MagicMock(first=chatbox)

    page.locator.side_effect = loc_mock

    handle_discussion(page, cfg)

    chatbox.click.assert_called_once()
    chatbox.press_sequentially.assert_called_once_with("ok", delay=50)
    reply_btn.click.assert_called_once_with(force=True)
    page.wait_for_timeout.assert_any_call(3000)
    page.wait_for_timeout.assert_any_call(5000)
    assert page.mouse.wheel.call_count == 12


def test_handle_discussion_advances_to_next_item() -> None:
    """Verify handle_discussion clicks 'Go to next item' CTA when visible."""
    page, cfg = MagicMock(), Settings()
    chatbox = MagicMock(is_visible=MagicMock(return_value=True))
    reply_btn = MagicMock(is_visible=MagicMock(return_value=True), is_enabled=MagicMock(return_value=True))
    reply_btn.get_attribute.return_value = "false"
    next_btn = MagicMock(is_visible=MagicMock(return_value=True))

    def loc_mock(s: str) -> MagicMock:
        if "next item" in s.lower():
            return MagicMock(first=next_btn)
        if "thread_reply" in s:
            return MagicMock(first=reply_btn)
        return MagicMock(first=chatbox)

    page.locator.side_effect = loc_mock

    handle_discussion(page, cfg)

    next_btn.click.assert_called_once_with(force=True)


def test_handle_discussion_bypasses_when_absent() -> None:
    """Verify handle_discussion exits gracefully when chatbox is absent."""
    page, cfg = MagicMock(), Settings()
    page.locator.return_value.first.is_visible.return_value = False
    handle_discussion(page, cfg)
