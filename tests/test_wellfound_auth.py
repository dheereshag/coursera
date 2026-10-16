"""Tests for Wellfound authentication and login flow."""

from unittest.mock import MagicMock

from playwright.sync_api import Error

from wellfound_automation.auth import (
    is_login_button_present,
    login_wellfound,
    submit_login_form,
)
from wellfound_automation.config import WellfoundConfig


def test_is_login_button_present_true() -> None:
    """Return True when login locator is visible."""
    page = MagicMock()
    page.locator.return_value.first.is_visible.return_value = True
    assert is_login_button_present(page) is True


def test_is_login_button_present_false() -> None:
    """Return False when login locator is not visible."""
    page = MagicMock()
    page.locator.return_value.first.is_visible.return_value = False
    assert is_login_button_present(page) is False


def test_is_login_button_present_exception() -> None:
    """Return False when locator visibility check raises an exception."""
    page = MagicMock()
    page.locator.return_value.first.is_visible.side_effect = Error("timeout")
    assert is_login_button_present(page) is False


def test_submit_login_form() -> None:
    """Verify input filling and submit button click."""
    page = MagicMock()
    cfg = WellfoundConfig(email="user@test.com", password="pass123")
    submit_login_form(page, cfg)

    # Check locator calls
    page.locator.assert_any_call('input#user_email, input[name="username"]')
    page.locator.assert_any_call('input#user_password, input[name="password"]')
    page.locator.assert_any_call('input[type="submit"][name="commit"], input.auth-btn--primary')


def test_login_wellfound_already_authenticated() -> None:
    """Skip login flow if login button is not present on home page."""
    page = MagicMock()
    page.locator.return_value.first.is_visible.return_value = False
    cfg = WellfoundConfig()

    result = login_wellfound(page, cfg)
    assert result is True
    page.goto.assert_called_once_with(cfg.base_url, wait_until="domcontentloaded")
    page.wait_for_timeout.assert_called_once_with(5000)


def test_login_wellfound_success() -> None:
    """Execute complete login flow when login button is present."""
    page = MagicMock()
    # First call is login button check on home page (True)
    # Second call is error check (False)
    page.locator.return_value.first.is_visible.return_value = True
    page.locator.return_value.is_visible.return_value = False
    cfg = WellfoundConfig()

    result = login_wellfound(page, cfg)
    assert result is True
    assert page.goto.call_count == 2
    page.goto.assert_any_call(cfg.base_url, wait_until="domcontentloaded")
    page.goto.assert_any_call(cfg.login_url, wait_until="domcontentloaded")


def test_login_wellfound_failure() -> None:
    """Return False when authentication error message is displayed."""
    page = MagicMock()
    page.locator.return_value.first.is_visible.return_value = True
    page.locator.return_value.is_visible.return_value = True
    page.locator.return_value.text_content.return_value = "Invalid email or password"
    cfg = WellfoundConfig()

    result = login_wellfound(page, cfg)
    assert result is False
