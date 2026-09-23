"""Weekly learning target modal handler: checks days, saves, and waits for reload."""

import logging
from contextlib import suppress

from playwright.sync_api import Error, Page

logger = logging.getLogger(__name__)
TARGET_SEL = '[data-testid="select-goal-days-step"], [aria-modal="true"]:has-text("weekly learning target")'
SAVE_BTN_SEL = '[data-testid="select-goal-days-btn-group"] button:has-text("Save"), button:has(span.cds-button-label:has-text("Save"))'


def handle_weekly_target(page: Page) -> bool:
    """Check all days, wait 5s for Save to enable, click Save, and wait 30s for reload."""
    if not page.locator(TARGET_SEL).first.is_visible(timeout=300):
        return False
    logger.info("Found 'Set your weekly learning target' modal. Checking all days...")
    cbs = page.locator('[data-testid="select-goal-days-step"] input[type="checkbox"]').all()
    for cb in cbs:
        with suppress(Error):
            if not cb.is_checked():
                cb.check(force=True)
    logger.info("Checked %d day(s). Waiting 5s for Save button to enable...", len(cbs))
    page.wait_for_timeout(5000)
    save_btn = page.locator(SAVE_BTN_SEL).first
    if save_btn.is_visible(timeout=3000):
        save_btn.click(force=True)
        logger.info("Clicked Save on weekly target. Waiting 30s for target setting and page reload...")
        page.wait_for_timeout(30000)
        with suppress(Error):
            page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(2000)
        return True
    return False
