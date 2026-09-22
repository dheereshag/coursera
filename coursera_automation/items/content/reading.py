"""Reading item automation: locate and click Mark as completed."""

import logging
import re

from playwright.sync_api import Page

from coursera_automation.config import Settings
from coursera_automation.items.navigation.dialogs import dismiss_dialogs

logger = logging.getLogger(__name__)
MARK_SEL = '[data-testid="mark-complete"], button:has(span.cds-button-label:has-text("Mark as completed")), button:has-text("Mark as completed")'


def handle_reading(page: Page, cfg: Settings) -> None:
    """Wait full 60s reading duration with scrolling, then click Mark as completed."""
    logger.info("Handling reading item: waiting full 60s reading time before completing...")
    page.wait_for_load_state("domcontentloaded")
    dismiss_dialogs(page)
    mark_btn = page.locator(MARK_SEL).or_(page.get_by_role("button", name=re.compile(r"mark as completed", re.IGNORECASE))).first

    if mark_btn.is_visible(timeout=1000):
        txt = mark_btn.inner_text().strip()
        if re.search(r"completed", txt, re.IGNORECASE) and not re.search(r"mark as", txt, re.IGNORECASE):
            logger.info("Reading item already completed (%s).", txt)
            return

    for c in range(12):
        page.mouse.wheel(0, 600)
        dismiss_dialogs(page)
        logger.info("Reading item in progress (%ds / 60s)...", (c + 1) * 5)
        page.wait_for_timeout(5000)

    page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(1000)
    dismiss_dialogs(page)
    if mark_btn.is_visible(timeout=5000):
        txt = mark_btn.inner_text().strip()
        if not (re.search(r"completed", txt, re.IGNORECASE) and not re.search(r"mark as", txt, re.IGNORECASE)):
            mark_btn.scroll_into_view_if_needed()
            mark_btn.click(force=True)
            logger.info("Clicked 'Mark as completed' after full 60s wait.")
            page.wait_for_timeout(3000)
    else:
        logger.info("'Mark as completed' button not present after 60s.")
