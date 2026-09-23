"""Dialog and overlay handlers: dismiss popups, honor code, and Pendo guides."""

import logging

from playwright.sync_api import Locator, Page

from .target import TARGET_SEL, handle_weekly_target

logger = logging.getLogger(__name__)

PENDO_SEL = '#pendo-guide-container, ._pendo-step-container-size, [id^="pendo-g-"]'
PENDO_BTN_SEL = 'button._pendo-close-guide, button[id^="pendo-close-guide"], button:has-text("Okay, got it"), #pendo-guide-container button'


def dismiss_pendo(page: Page) -> None:
    """Dismiss Pendo guide modal via close/confirm button with DOM fallback."""
    if (btn := page.locator(PENDO_BTN_SEL).first).is_visible(timeout=400):
        logger.info("Dismissing Pendo guide modal...")
        btn.click(force=True)
        page.wait_for_timeout(300)
    if (guide := page.locator(PENDO_SEL).first).is_visible(timeout=200):
        guide.evaluate('(el) => { el.closest("._pendo-step-container-size")?.remove() || el.remove(); }')


def dismiss_dialogs(page: Page) -> None:
    """Dismiss transient modals, popups, and sound effects prompts."""
    handle_weekly_target(page)
    dismiss_pendo(page)
    if (s := page.locator('div:has-text("sound effects") button').first).is_visible(timeout=400):
        s.click(force=True)
    if (honor := page.locator('[data-testid="HonorCodeModal"]').first).is_visible(timeout=400):
        if (c := honor.locator('input[type="checkbox"]').first).is_visible(timeout=200) and not c.is_checked():
            c.check(force=True)
        btn = honor.locator('button:has(span.cds-button-label:has-text("Continue")), button[aria-label*="close" i]').first
        btn = btn if btn.is_visible(timeout=200) else page.locator('button:has(span.cds-button-label:has-text("Continue"))').first
        if btn.is_visible(timeout=300):
            btn.click(force=True)
    if (att := page.locator('[data-testid="StartAttemptModal__primary-button"]').first).is_visible(timeout=400):
        logger.info("Dismissing attempt warning modal (Continue)...")
        att.click(force=True)
    for sel in ('.ab-close-button', 'button[aria-label*="close" i]', 'button:has-text("Got it")'):
        if (btn := page.locator(sel).first).is_visible(timeout=300):
            btn.click(force=True)
            break


def register_dialog_handlers(page: Page) -> None:
    """Register Playwright locator handlers for unexpected transient overlays."""
    def _handle_pendo(loc: Locator) -> None:
        btn = loc.locator(PENDO_BTN_SEL).first
        if btn.is_visible(timeout=500):
            btn.click(force=True)
        if loc.is_visible(timeout=200):
            loc.evaluate('(el) => { el.closest("._pendo-step-container-size")?.remove() || el.remove(); }')

    page.add_locator_handler(page.locator(PENDO_SEL).first, _handle_pendo)
    page.add_locator_handler(page.locator(TARGET_SEL).first, lambda loc: handle_weekly_target(loc.page))
