"""Reading item automation: locate and click Mark as completed."""

import logging
import re

from playwright.sync_api import Page

from coursera_automation.config import Settings
from coursera_automation.items.dialogs import dismiss_dialogs

logger = logging.getLogger(__name__)


def handle_reading(page: Page, cfg: Settings) -> None:
    """Scroll through reading item and click Mark as completed."""
    logger.info("Handling reading item...")
    page.wait_for_load_state("domcontentloaded")
    dismiss_dialogs(page)

    sel = (
        '[data-testid="mark-complete"], '
        'button:has(span.cds-button-label:has-text("Mark as completed")), '
        'button:has-text("Mark as completed")'
    )
    mark_btn = page.locator(sel).or_(page.get_by_role("button", name=re.compile(r"mark as completed", re.IGNORECASE))).first

    for _ in range(8):
        if mark_btn.is_visible():
            break
        page.mouse.wheel(0, 600)
        page.wait_for_timeout(300)

    dismiss_dialogs(page)
    if mark_btn.is_visible(timeout=3000):
        txt = mark_btn.inner_text().strip()
        if re.search(r"completed", txt, re.IGNORECASE) and not re.search(r"mark as", txt, re.IGNORECASE):
            logger.info("Reading item already completed (%s).", txt)
            return
        mark_btn.scroll_into_view_if_needed()
        mark_btn.click(force=True)
        logger.info("Clicked 'Mark as completed'.")
        page.wait_for_timeout(2000)
    else:
        logger.info("'Mark as completed' button already completed or not present.")
