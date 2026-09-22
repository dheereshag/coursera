"""Quiz submission handling and post-submission next-item navigation."""

import logging
import re

from playwright.sync_api import Error, Page

from coursera_automation.config import Settings

logger = logging.getLogger(__name__)
NEXT_BTN = '[data-testid="TopBannerCTAButton"], a:has-text("Next item"), button:has-text("Next item")'
MODAL_BTN = 'button[data-testid="dialog-submit-button"], [role="alertdialog"] button:has(span.cds-button-label:has-text("Submit")), [data-testid="AttemptViewSubmitControls__buttons"] button.cds-button-primary'


def poll_and_click_next(page: Page, max_wait_sec: int = 300) -> bool:
    """Poll until TopBannerCTAButton appears, reloading if pending, then click it."""
    logger.info("Polling for post-submission 'Next item' CTA (up to %ds)...", max_wait_sec)
    for cycle in range(max_wait_sec // 5):
        if (btn := page.locator(NEXT_BTN).first).is_visible(timeout=1000):
            href, orig = btn.get_attribute("href"), page.url
            try:
                btn.scroll_into_view_if_needed()
                btn.click(timeout=3000)
            except Error:
                btn.click(force=True)
            if page.url == orig and href:
                page.goto(href if href.startswith("http") else f"https://www.coursera.org{href}", wait_until="domcontentloaded")
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(3000)
            logger.info("Clicked 'Next item' after quiz submission.")
            return True
        if cycle > 0 and cycle % 6 == 0:
            logger.info("Evaluation pending; reloading page to refresh next item CTA...")
            page.reload(wait_until="domcontentloaded")
            page.wait_for_timeout(3000)
        else:
            page.wait_for_timeout(5000)
    logger.warning("Timed out after %ds waiting for 'Next item' CTA.", max_wait_sec)
    return False


def submit_quiz(page: Page, cfg: Settings) -> None:
    """Click submit button, confirm modal, and poll for next item CTA."""
    sub = page.get_by_role("button", name=re.compile(r"^submit", re.IGNORECASE)).first
    if not sub.is_visible(timeout=cfg.timeout_ms):
        return
    sub.scroll_into_view_if_needed()
    sub.click()
    page.wait_for_timeout(1500)
    if (modal := page.locator(MODAL_BTN).first).is_visible(timeout=5000):
        logger.info("Confirming submission in modal...")
        modal.click()
        try:
            modal.wait_for(state="hidden", timeout=5000)
        except Error:
            pass
    poll_and_click_next(page, max_wait_sec=300)
