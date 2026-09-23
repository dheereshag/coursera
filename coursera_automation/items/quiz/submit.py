"""Quiz submission handling and modal confirmation."""

import logging
import re

from playwright.sync_api import Error, Page

from coursera_automation.config import Settings
from coursera_automation.items.quiz.poll import NEXT_BTN, poll_and_click_next
from coursera_automation.items.quiz.status import is_final_exam

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
    wait_sec = max(0, cfg.post_quiz_wait_sec)
    if wait_sec:
        logger.info("Quiz submitted. Waiting %ds (3 mins) for evaluation and DOM stabilization...", wait_sec)
        for elapsed in range(30, wait_sec + 1, 30):
            page.wait_for_timeout(30000)
            logger.info("Post-quiz stabilization wait: %ds / %ds elapsed...", elapsed, wait_sec)
        if rem := wait_sec % 30:
            page.wait_for_timeout(rem * 1000)
    if is_final_exam(page):
        logger.info("Final Exam submitted. Skipping 'Next item' polling as no next item exists.")
        return
    poll_and_click_next(page, max_wait_sec=cfg.post_quiz_wait_sec)

