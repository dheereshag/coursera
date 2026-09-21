"""Status and completion detection for Coursera quiz assignments."""

import logging

from playwright.sync_api import Page

logger = logging.getLogger(__name__)


def is_quiz_completed(page: Page) -> bool:
    """Check if quiz is already passed and ready to advance without retry."""
    has_retry = page.locator('button:has-text("Try again")').first.is_visible(timeout=500)
    if has_retry:
        return False
    next_btn = page.locator(
        '[data-testid="TopBannerCTAButton"], a[role="button"]:has-text("Next item"), button:has-text("Next item")'
    ).first
    has_next = next_btn.is_visible(timeout=1000)
    has_passed = page.locator(
        'text=Passed, text="Grade received", text="You passed", text="Congratulations"'
    ).first.is_visible(timeout=500)
    return bool(has_next and has_passed)
