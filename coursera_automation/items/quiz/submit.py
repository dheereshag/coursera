"""Quiz submission handling, modal confirmation, and verification."""

import logging
from contextlib import suppress

from playwright.sync_api import Error, Locator, Page

from coursera_automation.config import Settings
from coursera_automation.items.quiz.poll import poll_and_click_next
from coursera_automation.items.quiz.status import is_final_exam

logger = logging.getLogger(__name__)
SUB_SEL = 'button[data-testid="submit-button"], button:has-text("Submit"):not([data-testid*="dialog"])'
MODAL_BTN = 'button[data-testid="dialog-submit-button"], [role="alertdialog"] button:has-text("Submit")'


def _click_btn(loc: Locator) -> None:
    with suppress(Error):
        loc.evaluate("el => el.scrollIntoView({block: 'center'})")
        loc.click(timeout=3000); return
    with suppress(Error):
        loc.evaluate("el => el.click()", timeout=2000)


def _confirm_modal(page: Page) -> None:
    modal = page.locator(MODAL_BTN).first
    with suppress(Error):
        modal.wait_for(state="visible", timeout=6000)
    for attempt in range(1, 4):
        if not modal.is_visible():
            break
        logger.info("Confirming submission in modal dialog (attempt %d)...", attempt)
        _click_btn(modal)
        page.wait_for_timeout(1500)
        with suppress(Error):
            modal.wait_for(state="hidden", timeout=3000)


def submit_quiz(page: Page, cfg: Settings) -> bool:
    """Click submit button, confirm dialog modal, and poll next item CTA."""
    sub = page.locator(SUB_SEL).first
    if not sub.is_visible(timeout=cfg.timeout_ms):
        logger.warning("Submit button not found on quiz page."); return False
    for _ in range(10):
        if sub.is_enabled() and sub.get_attribute("aria-disabled") != "true":
            break
        page.wait_for_timeout(500)
    _click_btn(sub)
    logger.info("Clicked quiz submit button. Waiting 3s for modal to mount...")
    page.wait_for_timeout(3000)
    _confirm_modal(page)
    logger.info("Quiz submitted. Waiting %ds for evaluation...", cfg.post_quiz_wait_sec)
    for elapsed in range(30, cfg.post_quiz_wait_sec + 1, 30):
        page.wait_for_timeout(30000)
        logger.info("Post-quiz wait: %ds / %ds elapsed...", elapsed, cfg.post_quiz_wait_sec)
    return True if is_final_exam(page) else poll_and_click_next(page, max_wait_sec=cfg.post_quiz_wait_sec)
