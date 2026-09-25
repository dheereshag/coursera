"""Quiz retry detection, button interaction, and attempt re-launching."""

import logging
from contextlib import suppress

from playwright.sync_api import Error, Locator, Page

logger = logging.getLogger(__name__)

RETRY_SELECTORS = (
    'button[data-testid="CoverPageActionButton"]:has-text("Retry")',
    'button[data-testid="CoverPageActionButton"]:has([data-testid="reload-icon"])',
    '[data-testid="CoverPageAction__controls"] button:has-text("Retry")',
    '[data-testid="CoverPageAction__controls"] button:has([data-testid="reload-icon"])',
    'button:has([data-testid="reload-icon"])',
    'button:has-text("Retry")',
    'button:has-text("Try again")',
)
CONFIRM_MODAL = '[data-testid="StartAttemptModal__primary-button"], [role="dialog"] button:has-text("Start attempt")'
ATTEMPT_READY = '[data-testid^="part-"], [data-testid="tunnel-vision-back-button"], button[aria-label="Back"], #agreement-checkbox-base'


def find_retry_button(page: Page) -> Locator | None:
    """Find visible retry button locator matching Coursera cover page CTAs."""
    for sel in RETRY_SELECTORS:
        if (btn := page.locator(sel).first).count() and btn.is_visible(timeout=300):
            return btn
    return None


def is_retry_available(page: Page) -> bool:
    """Return True if retry CTA is visible and not disabled by cooldown."""
    if not (btn := find_retry_button(page)):
        return False
    if btn.get_attribute("aria-disabled") == "true" or not btn.is_enabled():
        logger.warning("Retry button is disabled or on cooldown.")
        return False
    return True


def click_retry(page: Page) -> bool:
    """Click retry button, confirm start attempt modal if shown, and wait for attempt."""
    if not (btn := find_retry_button(page)) or btn.get_attribute("aria-disabled") == "true":
        return False
    logger.info("Clicking quiz Retry button: '%s'", btn.inner_text().strip())
    with suppress(Error):
        btn.scroll_into_view_if_needed(timeout=1000)
        btn.click(force=True, timeout=5000)
    page.wait_for_load_state("domcontentloaded")
    if (m := page.locator(CONFIRM_MODAL).first).is_visible(timeout=3000):
        with suppress(Error):
            m.click(force=True)
    with suppress(Error):
        page.locator(ATTEMPT_READY).first.wait_for(state="visible", timeout=8000)
    return True
