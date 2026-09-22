"""Launch quiz attempt: wait for and click CoverPageActionButton / start CTA."""

import logging
from contextlib import suppress

from playwright.sync_api import Error, Page

from coursera_automation.items.navigation.dialogs import dismiss_dialogs

from .status import is_quiz_completed

logger = logging.getLogger(__name__)

COVER_CTA = (
    '[data-testid="CoverPageActionButton"], [data-e2e="CoverPageActionButton"], '
    'button:has-text("Resume assignment"), button:has-text("Start assignment"), '
    'button:has-text("Resume"), button:has-text("Start")'
)
ATTEMPT_READY = '#agreement-checkbox-base, [data-testid*="submit"], button:has-text("Submit assignment")'
CONFIRM_MODAL = '[data-testid="StartAttemptModal__primary-button"], [role="dialog"] button:has-text("Start attempt")'


def is_on_cover_page(page: Page) -> bool:
    """Return whether the cover page action button is currently visible."""
    return page.locator('[data-testid="CoverPageActionButton"], [data-e2e="CoverPageActionButton"]').first.is_visible()


def ensure_quiz_launched(page: Page, timeout_ms: int = 15000) -> bool:
    """Wait for cover page CTA or active attempt, clicking launch/resume if present."""
    logger.info("Ensuring quiz attempt is launched...")
    page.wait_for_load_state("domcontentloaded")
    for _ in range(max(1, timeout_ms // 500)):
        dismiss_dialogs(page)
        if is_quiz_completed(page):
            return False
        cta = page.locator(COVER_CTA).first
        if cta.count() and cta.is_visible() and cta.get_attribute("aria-disabled") != "true":
            logger.info("Clicking quiz cover page CTA: '%s'", cta.inner_text().strip())
            with suppress(Error):
                cta.scroll_into_view_if_needed(timeout=1000)
                cta.click(force=True, timeout=5000)
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(1000)
            dismiss_dialogs(page)
            if (modal := page.locator(CONFIRM_MODAL).first).is_visible():
                modal.click(force=True)
            with suppress(Error):
                cta.wait_for(state="hidden", timeout=8000)
                return True
        if page.locator(ATTEMPT_READY).first.is_visible():
            return True
        page.wait_for_timeout(500)
    return False
