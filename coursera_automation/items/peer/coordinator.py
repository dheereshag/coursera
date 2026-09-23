"""Peer-graded assignment orchestration: tab selection, title, upload, and submit."""

import logging
from pathlib import Path

from playwright.sync_api import Page

from coursera_automation.config import Settings
from coursera_automation.items.navigation.dialogs import dismiss_dialogs
from coursera_automation.items.peer.upload import upload_peer_file
from coursera_automation.items.quiz.poll import poll_and_click_next

logger = logging.getLogger(__name__)
SUB_TAB = 'button[role="tab"]:has-text("My submission"), button:has-text("My submission")'
TITLE_INP = 'input#title, input[aria-label="Project Title"], input[placeholder*="title" i]'
SUBMIT_BTN = 'button[data-testid="preview"], button[data-track-component="submit"], button[aria-label="Submit"]'
MODAL_BTN = 'button[data-testid="dialog-submit-button"], [role="alertdialog"] button:has-text("Submit")'
HONOR_SEL = '#agreement-checkbox-base, [aria-label*="Honor Code" i] input, label:has-text("Honor Code"), label:has-text("understand and agree")'


def _submit_and_confirm(page: Page, max_wait: int = 120) -> None:
    """Poll for submit readiness up to max_wait, click submit, and confirm modal."""
    logger.info("Polling for submit button readiness (up to %ds)...", max_wait)
    sub = page.locator(SUBMIT_BTN).first
    for c in range(max(1, max_wait // 5)):
        if sub.is_visible(timeout=1000) and sub.is_enabled() and sub.get_attribute("aria-disabled") != "true":
            logger.info("Submit button enabled; submitting project...")
            break
        page.wait_for_timeout(5000)
    if (chk := page.locator(HONOR_SEL).first).is_visible(timeout=2000) and not (
        chk.is_checked() if chk.get_attribute("type") == "checkbox" else False
    ):
        logger.info("Checking Honor Code agreement checkbox...")
        chk.click(force=True)
    sub.click(force=True)
    page.wait_for_timeout(2000)
    if (modal := page.locator(MODAL_BTN).first).is_visible(timeout=15000):
        logger.info("Confirming submission in modal...")
        modal.click()
        page.wait_for_timeout(2000)


def handle_peer(page: Page, cfg: Settings) -> None:
    """Handle peer-graded assignment lifecycle."""
    logger.info("Handling peer-graded assignment (10s load wait)...")
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(10000)
    dismiss_dialogs(page)
    if (tab := page.locator(SUB_TAB).first).is_visible(timeout=5000):
        tab.click()
        page.wait_for_timeout(2000)
    if (inp := page.locator(TITLE_INP).first).is_visible(timeout=5000):
        inp.fill("test")
        page.wait_for_timeout(1000)
    upload_peer_file(page, Path("test.png").resolve())
    _submit_and_confirm(page, max_wait=120)
    poll_and_click_next(page, max_wait_sec=cfg.post_quiz_wait_sec)

