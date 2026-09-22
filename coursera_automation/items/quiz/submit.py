"""Quiz submission handling and post-submission next-item navigation."""

import logging
import re

from playwright.sync_api import Error, Page

from coursera_automation.config import Settings

logger = logging.getLogger(__name__)
NEXT_BTN = '[data-testid="TopBannerCTAButton"]'
MODAL_BTN = 'button[data-testid="dialog-submit-button"], [role="alertdialog"] button:has(span.cds-button-label:has-text("Submit")), [data-testid="AttemptViewSubmitControls__buttons"] button.cds-button-primary'


def poll_and_click_next(page: Page, max_wait_sec: int = 300) -> bool:
    """Poll every 5s until TopBannerCTAButton mounts, then click it to advance URL."""
    logger.info("Polling every 5s for 'Next item' CTA (up to %ds)...", max_wait_sec)
    orig = page.url
    for cycle in range(max(1, max_wait_sec // 5)):
        if (btn := page.locator(NEXT_BTN).first).is_visible(timeout=1000):
            href = btn.get_attribute("href") or ""
            try:
                btn.scroll_into_view_if_needed()
                btn.click(timeout=3000)
            except Error:
                btn.click(force=True)
            page.wait_for_timeout(2000)
            if page.url == orig and href:
                page.goto(href if href.startswith("http") else f"https://www.coursera.org{href}", wait_until="domcontentloaded")
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(2000)
            if page.url != orig:
                logger.info("Successfully advanced to next item: %s", page.url)
                return True
        if cycle > 0 and cycle % 6 == 0:
            logger.info("Waiting for evaluation; reloading page to refresh CTA...")
            page.reload(wait_until="domcontentloaded")
            page.wait_for_timeout(3000)
        else:
            page.wait_for_timeout(5000)
    logger.warning("Timed out after %ds waiting for 'Next item' CTA.", max_wait_sec)
    return page.url != orig


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
