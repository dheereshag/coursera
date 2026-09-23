"""Sequential item progression navigation controls."""

from contextlib import suppress

from playwright.sync_api import Error, Page

from coursera_automation.config import Settings
from coursera_automation.items.navigation.dialogs import dismiss_dialogs
from coursera_automation.items.navigation.resume import click_resume

__all__ = ["click_next_item", "click_resume"]


def click_next_item(page: Page, cfg: Settings) -> bool:
    """Locate and click 'Next item' or navigate directly via href."""
    orig = page.url
    has_back = page.locator('[data-testid="tunnel-vision-back-button"], button[aria-label="Back"]').first.is_visible(timeout=300)
    if has_back:
        top = page.locator('[data-testid="TopBannerCTAButton"]').first
        if not top.is_visible(timeout=1000):
            return not page.locator('#agreement-checkbox-base, [id^="prompt-autoGradableResponseId"]').first.is_visible(timeout=300) and False
        btn_cand = [top]
    else:
        btn_cand = []
    for _ in range(1 if has_back else 8):
        dismiss_dialogs(page)
        if not btn_cand:
            locs = page.locator('[data-testid*="next-item"], button:has-text("Next item"), a:has-text("Next item")')
            btn_cand = [b for b in [next((l for l in locs.all() if l.is_visible()), None) or (locs.first if locs.first.is_visible() else None)] if b]
        if btn_cand:
            btn = btn_cand[0]
            with suppress(Error):
                btn.click(force=True, timeout=3000)
            page.wait_for_timeout(1500)
            if page.url == orig and (href := btn.get_attribute("href")):
                target = href if href.startswith("http") else f"https://www.coursera.org{href}"
                page.goto(target, wait_until="domcontentloaded")
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(2000)
            dismiss_dialogs(page)
            if page.url != orig:
                return True
        page.mouse.wheel(0, 400)
        page.wait_for_timeout(1000)
    return False
