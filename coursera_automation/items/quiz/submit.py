"""Quiz submission handling and modal confirmation."""

import logging
import re

from playwright.sync_api import Error, Page

from coursera_automation.config import Settings
from coursera_automation.items.quiz.poll import NEXT_BTN, poll_and_click_next

__all__ = ["MODAL_BTN", "NEXT_BTN", "poll_and_click_next", "submit_quiz"]

logger = logging.getLogger(__name__)
MODAL_BTN = 'button[data-testid="dialog-submit-button"], [role="alertdialog"] button:has(span.cds-button-label:has-text("Submit")), [data-testid="AttemptViewSubmitControls__buttons"] button.cds-button-primary'


def submit_quiz(page: Page, cfg: Settings) -> None:
    """Click submit button, confirm modal, and poll for next item CTA."""
    sub = page.get_by_role("button", name=re.compile(r"^submit", re.IGNORECASE)).first
    if not sub.is_visible(timeout=cfg.timeout_ms):
        return
    sub.scroll_into_view_if_needed()
    for _ in range(10):
        if sub.is_enabled() and sub.get_attribute("aria-disabled") != "true":
            break
        page.wait_for_timeout(500)
    sub.click(force=True)
    page.wait_for_timeout(1500)
    if (modal := page.locator(MODAL_BTN).first).is_visible(timeout=5000):
        logger.info("Confirming submission in modal...")
        modal.click()
        try:
            modal.wait_for(state="hidden", timeout=5000)
        except Error:
            pass
    poll_and_click_next(page, max_wait_sec=300)

