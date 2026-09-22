"""Navigation controls: resume, next item progression, and dialog dismissal."""

import logging
import re

from playwright.sync_api import Error, Page

from coursera_automation.config import Settings
from coursera_automation.items.navigation.dialogs import dismiss_dialogs

logger = logging.getLogger(__name__)
NEXT_SEL = '[data-testid="TopBannerCTAButton"], [data-testid*="next-item"], button:has-text("Next item"), a:has-text("Next item")'


def click_resume(page: Page, cfg: Settings) -> None:
    """Scroll vertically and click Resume or Get started on course view."""
    dismiss_dialogs(page)
    res = page.locator('button, a, [role="button"]').filter(has=page.locator("span.cds-button-label", has_text=re.compile(r"resume", re.IGNORECASE))).first
    start = page.locator('button, a, [role="button"]').filter(has_text=re.compile(r"get started", re.IGNORECASE)).first
    btn = None
    for _ in range(8):
        if (btn := res if res.is_visible() else (start if start.is_visible() else None)):
            break
        page.mouse.wheel(0, 500)
        page.wait_for_timeout(400)
    btn = btn or (res if res.is_visible(timeout=1000) else start)
    btn.wait_for(state="visible", timeout=cfg.timeout_ms)
    btn.click(force=True)
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(10000)
    dismiss_dialogs(page)


def click_next_item(page: Page, cfg: Settings) -> bool:
    """Locate and click 'Next item' or navigate directly via href."""
    orig = page.url
    for _ in range(8):
        dismiss_dialogs(page)
        if page.locator(':text("Reviewing your submission"), :text("hang tight")').first.is_visible(timeout=300):
            page.wait_for_timeout(3000)
            continue
        locs = page.locator(NEXT_SEL)
        if (btn := next((l for l in locs.all() if l.is_visible()), None) or (locs.first if locs.first.is_visible() else None)):
            logger.info("Advancing via next item button...")
            try:
                btn.scroll_into_view_if_needed()
                btn.click(timeout=3000)
            except Error:
                btn.click(force=True)
            page.wait_for_timeout(1500)
            if page.url == orig and (href := btn.get_attribute("href")):
                page.goto(href if href.startswith("http") else f"https://www.coursera.org{href}", wait_until="domcontentloaded")
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(2000)
            dismiss_dialogs(page)
            if page.url != orig:
                return True
        page.mouse.wheel(0, 400)
        page.wait_for_timeout(1000)
    return False
