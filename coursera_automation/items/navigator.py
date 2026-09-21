"""Navigation controls: resume, next item progression, and dialog dismissal."""

import logging
import re

from playwright.sync_api import Page

from coursera_automation.config import Settings
from coursera_automation.items.dialogs import dismiss_dialogs

logger = logging.getLogger(__name__)
NEXT_SEL = (
    '[data-testid="TopBannerCTAButton"], [data-testid*="next-item"], '
    'button:has-text("Next item"), a:has-text("Next item"), button:has-text("Go to next item")'
)


def click_resume(page: Page, cfg: Settings) -> None:
    """Scroll vertically and click Resume or Get started on course view."""
    dismiss_dialogs(page)
    res = page.locator('button, a, [role="button"]').filter(
        has=page.locator("span.cds-button-label", has_text=re.compile(r"resume", re.IGNORECASE))
    ).first
    start = page.locator('button, a, [role="button"], span.cds-button-label').filter(
        has_text=re.compile(r"get started", re.IGNORECASE)
    ).first
    btn = None
    for _ in range(8):
        if res.is_visible():
            btn = res
            break
        if start.is_visible():
            btn = start
            break
        page.mouse.wheel(0, 500)
        page.wait_for_timeout(400)
    btn = btn or (res if res.is_visible(timeout=1000) else start)
    btn.wait_for(state="visible", timeout=cfg.timeout_ms)
    logger.info("Clicking course resume/start CTA...")
    btn.click(force=True)
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(10000)
    dismiss_dialogs(page)


def click_next_item(page: Page, cfg: Settings) -> bool:
    """Locate and click 'Next item' or 'Go to next item' progression button."""
    for _ in range(5):
        dismiss_dialogs(page)
        if (btn := page.locator(NEXT_SEL).first).is_visible(timeout=1000):
            logger.info("Advancing via next item button...")
            btn.click(force=True)
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(10000)
            dismiss_dialogs(page)
            return True
        page.mouse.wheel(0, 400)
        page.wait_for_timeout(1000)
    return False
