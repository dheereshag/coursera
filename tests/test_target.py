"""Unit tests for weekly learning target modal automation."""

from unittest.mock import MagicMock

from coursera_automation.items.navigation.target import (
    SAVE_BTN_SEL,
    TARGET_SEL,
    handle_weekly_target,
)


def test_handle_weekly_target_absent() -> None:
    """Verify handle_weekly_target returns False when target modal is not visible."""
    page = MagicMock()
    page.locator.return_value.first.is_visible.return_value = False
    assert handle_weekly_target(page) is False
    page.wait_for_timeout.assert_not_called()


def test_handle_weekly_target_present() -> None:
    """Verify handle_weekly_target checks days, waits 5s, clicks Save, and waits 30s."""
    page = MagicMock()
    target_loc = MagicMock(is_visible=MagicMock(return_value=True))
    save_btn = MagicMock(is_visible=MagicMock(return_value=True))
    cb1 = MagicMock(is_checked=MagicMock(return_value=False))
    cb2 = MagicMock(is_checked=MagicMock(return_value=True))

    def locator_side_effect(s: str) -> MagicMock:
        if s == TARGET_SEL:
            return MagicMock(first=target_loc)
        if "checkbox" in s:
            return MagicMock(all=MagicMock(return_value=[cb1, cb2]))
        if s == SAVE_BTN_SEL:
            return MagicMock(first=save_btn)
        return MagicMock(first=MagicMock(is_visible=MagicMock(return_value=False)))

    page.locator.side_effect = locator_side_effect
    assert handle_weekly_target(page) is True
    cb1.check.assert_called_once_with(force=True)
    cb2.check.assert_not_called()
    save_btn.click.assert_called_once_with(force=True)
    page.wait_for_timeout.assert_any_call(5000)
    page.wait_for_timeout.assert_any_call(30000)
    page.wait_for_load_state.assert_called_with("domcontentloaded")


def test_handle_weekly_target_save_btn_absent() -> None:
    """Verify handle_weekly_target returns False if Save button is not visible."""
    page = MagicMock()
    target_loc = MagicMock(is_visible=MagicMock(return_value=True))
    save_btn = MagicMock(is_visible=MagicMock(return_value=False))

    def locator_side_effect(s: str) -> MagicMock:
        if s == TARGET_SEL:
            return MagicMock(first=target_loc)
        if "checkbox" in s:
            return MagicMock(all=MagicMock(return_value=[]))
        if s == SAVE_BTN_SEL:
            return MagicMock(first=save_btn)
        return MagicMock(first=MagicMock(is_visible=MagicMock(return_value=False)))

    page.locator.side_effect = locator_side_effect
    assert handle_weekly_target(page) is False
    save_btn.click.assert_not_called()
