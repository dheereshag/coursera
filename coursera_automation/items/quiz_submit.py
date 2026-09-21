"""Quiz submission handling and post-submission evaluation waiting."""

import logging
import re

from playwright.sync_api import Error, Page

from coursera_automation.config import Settings

logger = logging.getLogger(__name__)


def _wait_for_evaluation(page: Page, max_wait_sec: int = 300) -> None:
    """Poll up to max_wait_sec for Coursera quiz grading to complete."""
    logger.info("Waiting for quiz evaluation (up to %ds)...", max_wait_sec)
    done_sel = (
        '[data-testid="TopBannerCTAButton"], button:has-text("Next item"), '
        'a:has-text("Next item"), button:has-text("Try again"), '
        ':text("Your grade:"), :text("Passed"), :text("Grade received")'
    )
    for cycle in range(max_wait_sec // 5):
        if page.locator(done_sel).first.is_visible(timeout=1000):
            logger.info("Quiz evaluation completed.")
            return
        if cycle > 0 and cycle % 9 == 0:
            logger.info("Evaluation in progress; reloading page to refresh grade...")
            page.reload(wait_until="domcontentloaded")
            page.wait_for_timeout(2000)
        else:
            page.wait_for_timeout(5000)
    logger.warning("Quiz evaluation wait reached %ds timeout.", max_wait_sec)


def submit_quiz(page: Page, cfg: Settings) -> None:
    """Click submit button, confirm in modal, and wait for grading."""
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
    _wait_for_evaluation(page, max_wait_sec=300)
    page.wait_for_timeout(2000)
