"""Quiz submission handling including confirmation modal interactions."""

import logging
import re

from playwright.sync_api import Error, Page

from coursera_automation.config import Settings

logger = logging.getLogger(__name__)


def submit_quiz(page: Page, cfg: Settings) -> None:
    """Click submit button and confirm in submission modal if present."""
    sub = page.get_by_role("button", name=re.compile(r"^submit", re.IGNORECASE)).first
    if not sub.is_visible(timeout=cfg.timeout_ms):
        return

    sub.scroll_into_view_if_needed()
    sub.click()
    page.wait_for_timeout(1500)
    modal_btn = page.locator(
        'button[data-testid="dialog-submit-button"], '
        '[role="alertdialog"] button:has(span.cds-button-label:has-text("Submit")), '
        '[data-testid="AttemptViewSubmitControls__buttons"] button.cds-button-primary'
    ).first
    if modal_btn.is_visible(timeout=5000):
        logger.info("Confirming submission in modal...")
        modal_btn.click()
        try:
            page.locator('[role="alertdialog"], button[data-testid="dialog-submit-button"]').first.wait_for(
                state="hidden", timeout=5000
            )
        except Error as exc:
            logger.debug("Modal dismissal wait: %s", exc)
    try:
        page.locator('[data-testid="TopBannerCTAButton"], [data-testid="assignment-view-tunnel-vision"]').first.wait_for(
            state="visible", timeout=cfg.timeout_ms
        )
    except Error:
        pass
    page.wait_for_timeout(3000)



