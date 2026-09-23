"""Polling and navigation for post-quiz next item CTA."""

import logging

from playwright.sync_api import Error, Page

logger = logging.getLogger(__name__)
BACK_BTN = '[data-testid="tunnel-vision-back-button"], button[aria-label="Back"]'
TOP_CTA = '[data-testid="TopBannerCTAButton"]'
NEXT_BTN = '[data-testid*="next-item"], button:has-text("Go to next item"), button:has-text("Next item"), a:has-text("Next item")'


def poll_and_click_next(page: Page, max_wait_sec: int = 300) -> bool:
    """Poll for back button, then check and click TopBannerCTAButton to advance URL."""
    logger.info("Polling every 5s for 'Next item' CTA (up to %ds)...", max_wait_sec)
    orig = page.url
    for cycle in range(max(1, max_wait_sec // 5)):
        elapsed = (cycle + 1) * 5
        has_back = page.locator(BACK_BTN).first.is_visible(timeout=500)
        btn = page.locator(TOP_CTA).first if has_back else page.locator(NEXT_BTN).first
        if btn.is_visible(timeout=1000):
            logger.info("Found 'Next item' CTA (has_back=%s). Attempting to click...", has_back)
            href = btn.get_attribute("href") or ""
            try:
                btn.click(timeout=3000)
            except Error:
                btn.click(force=True)
            page.wait_for_timeout(2000)
            if page.url == orig and href:
                target = href if href.startswith("http") else f"https://www.coursera.org{href}"
                page.goto(target, wait_until="domcontentloaded")
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(2000)
            if page.url != orig:
                logger.info("Successfully advanced to next item: %s", page.url)
                return True
            logger.info("Clicked CTA but URL did not change yet (current: %s).", page.url)
        else:
            logger.info("'Next item' CTA not visible yet (waited %ds / %ds); retrying in 5s...", elapsed, max_wait_sec)
        page.wait_for_timeout(5000)
    logger.warning("Timed out after %ds waiting for 'Next item' CTA.", max_wait_sec)
    return page.url != orig
