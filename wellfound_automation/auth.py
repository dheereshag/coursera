"""Wellfound authentication and login flow."""

import logging

from playwright.sync_api import Error, Page

from wellfound_automation.config import WellfoundConfig

logger = logging.getLogger(__name__)


def is_login_button_present(page: Page) -> bool:
    """Check if the login button is present on the page."""
    login_btn = page.locator('a[href*="/login"], a.login').first
    try:
        return login_btn.is_visible(timeout=3000)
    except Error:
        return False


def submit_login_form(page: Page, cfg: WellfoundConfig) -> None:
    """Fill email and password credentials, then submit."""
    logger.info("Filling credentials and submitting form...")
    page.locator('input#user_email, input[name="username"]').fill(cfg.email)
    page.locator('input#user_password, input[name="password"]').fill(cfg.password)
    page.locator('input[type="submit"][name="commit"], input.auth-btn--primary').click()


def login_wellfound(page: Page, cfg: WellfoundConfig) -> bool:
    """Navigate to Wellfound and perform login if needed."""
    logger.info("Navigating to %s...", cfg.base_url)
    page.goto(cfg.base_url, wait_until="domcontentloaded")
    page.wait_for_timeout(5000)

    if not is_login_button_present(page):
        logger.info("Login button not found. Already logged in!")
        return True

    logger.info("Login button found. Opening %s...", cfg.login_url)
    page.goto(cfg.login_url, wait_until="domcontentloaded")
    page.wait_for_timeout(3000)

    submit_login_form(page, cfg)
    page.wait_for_timeout(5000)

    err = page.locator(".auth-errors:not([hidden])")
    if err.is_visible(timeout=2000):
        logger.error("Login error detected: %s", err.text_content())
        return False

    logger.info("Login submitted successfully.")
    return True
