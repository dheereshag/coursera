"""Coursera login automation steps."""

import logging
import re

from playwright.sync_api import Page

from coursera_automation.config import Settings

logger = logging.getLogger(__name__)


def wait_for_auth_complete(page: Page) -> None:
    """Wait for user to solve puzzle and verify login session."""
    logger.info("Please solve the puzzle in the browser window if shown...")
    for _ in range(180):
        cookies = {c["name"]: c["value"] for c in page.context.cookies()}
        has_cauth = bool(cookies.get("CAUTH"))
        prof = page.locator('button[data-e2e="header-profile-menu"]').first
        dialog = page.locator('div[role="dialog"]').first

        if (has_cauth or prof.is_visible()) and not dialog.is_visible():
            logger.info("Authentication verified! Proceeding to course...")
            return
        page.wait_for_timeout(1000)
    logger.warning("Auth wait timeout reached. Continuing...")


def login(page: Page, cfg: Settings) -> None:
    """Navigate to coursera.org and authenticate only if not already logged in."""
    logger.info("Opening home URL: %s", cfg.login_url)
    page.goto(cfg.login_url, wait_until="domcontentloaded")

    login_btn = (
        page.get_by_role("button", name=re.compile(r"^log in$", re.IGNORECASE))
        .or_(page.get_by_role("link", name=re.compile(r"^log in$", re.IGNORECASE)))
        .first
    )
    if not login_btn.is_visible(timeout=4000):
        logger.info("Already authenticated. Skipping login modal.")
        return

    logger.info("Clicking Log In...")
    login_btn.click()
    email_in = page.locator('input[placeholder="name@email.com"]')
    email_in.wait_for(state="visible", timeout=cfg.timeout_ms)
    email_in.fill(cfg.email)
    page.get_by_role("button", name="Continue", exact=True).first.click()

    pwd_in = page.locator('input[type="password"]')
    pwd_in.wait_for(state="visible", timeout=cfg.timeout_ms)
    pwd_in.fill(cfg.password)
    page.get_by_role("button", name="Next", exact=True).first.click()

    wait_for_auth_complete(page)
    page.wait_for_timeout(2000)
