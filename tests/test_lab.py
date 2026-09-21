"""Unit tests for lab handling: agreement check, scroll, and launch."""

from unittest.mock import MagicMock, patch

from coursera_automation.config import Settings
from coursera_automation.items.lab import _check_agreement, handle_lab


def test_check_agreement_flow() -> None:
    """Verify _check_agreement clicks label and falls back to check."""
    page = MagicMock()
    inp = MagicMock(is_visible=MagicMock(return_value=False), is_checked=MagicMock(side_effect=[False, False, True]))
    lbl = MagicMock(is_visible=MagicMock(return_value=True))
    page.locator.side_effect = lambda s: MagicMock(first=inp if "input" in s else lbl)
    _check_agreement(page)
    lbl.click.assert_called_once_with(force=True)
    inp.check.assert_called_once_with(force=True)


def test_handle_lab_scroll_and_launch() -> None:
    """Verify handle_lab scrolls and clicks launch button."""
    page, cfg = MagicMock(), Settings()
    btn = MagicMock(is_disabled=MagicMock(return_value=False))
    page.locator.return_value.or_.return_value.first = btn
    popup = MagicMock()
    page.expect_popup.return_value.__enter__.return_value.value = popup
    with (
        patch("coursera_automation.items.lab._check_agreement") as mock_agree,
        patch("coursera_automation.items.lab.dismiss_dialogs"),
    ):
        handle_lab(page, cfg)
        assert mock_agree.call_count >= 1
        btn.wait_for.assert_called_once_with(state="visible", timeout=10000)
        btn.click.assert_called_once_with(force=True)
        assert page.mouse.wheel.call_count == 4
        page.evaluate.assert_any_call("() => window.scrollTo(0, document.body.scrollHeight)")
        popup.wait_for_load_state.assert_called_once_with("domcontentloaded")
        page.wait_for_timeout.assert_any_call(10000)
        page.bring_to_front.assert_called_once()


def test_handle_lab_mark_completed() -> None:
    """Verify handle_lab clicks Mark as completed if available on lab."""
    page, cfg = MagicMock(), Settings()
    btn = MagicMock(is_visible=MagicMock(return_value=False))
    mark = MagicMock(is_visible=MagicMock(return_value=True), inner_text=MagicMock(return_value="Mark as completed"))
    page.locator.side_effect = lambda s: MagicMock(
        first=mark if "mark-complete" in s else btn,
        or_=MagicMock(return_value=MagicMock(first=btn)),
    )
    with (
        patch("coursera_automation.items.lab._check_agreement"),
        patch("coursera_automation.items.lab.dismiss_dialogs"),
    ):
        handle_lab(page, cfg)
        mark.click.assert_called_once_with(force=True)
