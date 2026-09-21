"""Unit tests for dialog, popup, and Pendo guide dismissal."""

from unittest.mock import MagicMock

from coursera_automation.items.dialogs import (
    PENDO_BTN_SEL,
    PENDO_SEL,
    dismiss_dialogs,
    dismiss_pendo,
    register_dialog_handlers,
)


def test_dismiss_pendo_clicks_button() -> None:
    """Verify dismiss_pendo clicks the Pendo guide button when visible."""
    page = MagicMock()
    btn, guide = MagicMock(), MagicMock()
    btn.first.is_visible.return_value = True
    guide.first.is_visible.return_value = False
    page.locator.side_effect = lambda s: btn if s == PENDO_BTN_SEL else guide

    dismiss_pendo(page)
    btn.first.click.assert_called_once_with(force=True)
    guide.first.evaluate.assert_not_called()


def test_dismiss_pendo_evaluates_fallback() -> None:
    """Verify dismiss_pendo removes guide from DOM if still visible."""
    page = MagicMock()
    btn, guide = MagicMock(), MagicMock()
    btn.first.is_visible.return_value = False
    guide.first.is_visible.return_value = True
    page.locator.side_effect = lambda s: btn if s == PENDO_BTN_SEL else guide

    dismiss_pendo(page)
    btn.first.click.assert_not_called()
    guide.first.evaluate.assert_called_once()


def test_dismiss_dialogs_orchestrates_all() -> None:
    """Verify dismiss_dialogs clicks Continue on StartAttemptModal."""
    page, att = MagicMock(), MagicMock()
    att.first.is_visible.return_value = True
    page.locator.side_effect = lambda s: att if "StartAttemptModal" in s else MagicMock(first=MagicMock(is_visible=lambda timeout=0: False))
    dismiss_dialogs(page)
    att.first.click.assert_called_once_with(force=True)


def test_register_dialog_handlers() -> None:
    """Verify register_dialog_handlers registers locator handler on page."""
    page = MagicMock()
    register_dialog_handlers(page)
    page.add_locator_handler.assert_called_once()
    args, _ = page.add_locator_handler.call_args
    assert args[0] == page.locator(PENDO_SEL).first
