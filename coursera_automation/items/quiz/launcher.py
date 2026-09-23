"""Launch quiz attempt: wait for and click CoverPageActionButton / start CTA."""

import logging
from contextlib import suppress

from playwright.sync_api import Error, Locator, Page

from coursera_automation.items.navigation.dialogs import dismiss_dialogs

from .status import is_quiz_completed

logger = logging.getLogger(__name__)

ATTEMPT_READY = '[data-testid="tunnel-vision-back-button"], button[aria-label="Back"], #agreement-checkbox-base, textarea:not([disabled]), button:has-text("Save draft")'
CONFIRM_MODAL = '[data-testid="StartAttemptModal__primary-button"], [role="dialog"] button:has-text("Start attempt")'
COVER_SELECTORS = ('button[data-testid="CoverPageActionButton"], button[data-e2e="CoverPageActionButton"]', 'button:has-text("Resume"), button:has-text("Start"), button:has-text("Try again"), a:has-text("Try again")')


def _find_cover_cta(page: Page) -> Locator | None:
    for sel in COVER_SELECTORS:
        if (
            (cta := page.locator(sel).first).count()
            and cta.is_visible()
            and "target" not in cta.inner_text().lower()
            and ("try again" in cta.inner_text().lower() or not page.locator(ATTEMPT_READY).first.is_visible(timeout=300))
        ):
            return cta
    return None


def is_on_cover_page(page: Page) -> bool:
    """Return whether the cover page action button is currently visible."""
    return _find_cover_cta(page) is not None


def ensure_quiz_launched(page: Page, timeout_ms: int = 15000) -> bool:
    """Wait for cover page CTA or active attempt, clicking launch/resume if present."""
    logger.info("Ensuring quiz attempt is launched...")
    page.wait_for_load_state("domcontentloaded")
    for _ in range(max(1, timeout_ms // 500)):
        dismiss_dialogs(page)
        if (cta := _find_cover_cta(page)) and cta.get_attribute("aria-disabled") != "true":
            logger.info("Clicking quiz cover page CTA: '%s'", cta.inner_text().strip())
            with suppress(Error):
                cta.scroll_into_view_if_needed(timeout=1000)
                cta.click(force=True, timeout=5000)
            page.wait_for_load_state("domcontentloaded")
            dismiss_dialogs(page)
            if (m := page.locator(CONFIRM_MODAL).first).is_visible():
                m.click(force=True)
            with suppress(Error):
                page.locator(ATTEMPT_READY).first.wait_for(state="visible", timeout=8000)
            return True
        if page.locator(ATTEMPT_READY).first.is_visible(timeout=300):
            return True
        if is_quiz_completed(page):
            return False
        page.wait_for_timeout(500)
    return False
