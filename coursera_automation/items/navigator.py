"""Navigation controls: resume, next item progression, and dialog dismissal."""

import logging
import re

from playwright.sync_api import Page

from coursera_automation.config import Settings
from coursera_automation.items.dialogs import dismiss_dialogs

logger = logging.getLogger(__name__)


def click_resume(page: Page, cfg: Settings) -> None:
    """Scroll vertically and click Resume button on course view."""
    dismiss_dialogs(page)
    lbl = page.locator("span.cds-button-label", has_text=re.compile(r"resume", re.IGNORECASE))
    btn = page.locator('button, [role="button"]').filter(has=lbl).first
    for _ in range(8):
        if btn.is_visible():
            break
        page.mouse.wheel(0, 500)
        page.wait_for_timeout(400)
    btn.wait_for(state="visible", timeout=cfg.timeout_ms)
    logger.info("Clicking course resume/start CTA...")
    btn.click()
    page.wait_for_timeout(3000)
    dismiss_dialogs(page)


def click_next_item(page: Page, cfg: Settings) -> bool:
    """Locate and click 'Next item' or 'Go to next item' progression button."""
    sel = '[data-testid="TopBannerCTAButton"], button:has(span.cds-button-label:has-text("Next item")), a:has(span.cds-button-label:has-text("Next item")), button:has-text("Next item"), a:has-text("Next item"), [data-testid*="next-item"]'
    for _ in range(5):
        dismiss_dialogs(page)
        if (btn := page.locator(sel).first).is_visible(timeout=1000):
            logger.info("Advancing via next item button...")
            btn.click(force=True)
            page.wait_for_timeout(3000)
            return True
        page.mouse.wheel(0, 400)
        page.wait_for_timeout(1000)
    return False

