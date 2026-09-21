"""Status and completion detection for Coursera quiz assignments."""

import logging

from playwright.sync_api import Page

logger = logging.getLogger(__name__)


def is_quiz_completed(page: Page) -> bool:
    """Check if quiz is already passed or in review mode without retry."""
    if page.locator(':text("Reviewing your submission"), :text("hang tight")').first.is_visible(timeout=500):
        return False
    if page.locator('button:has-text("Try again")').first.is_visible(timeout=500):
        return False
    has_passed = page.locator(
        ':text("Your grade:"), :text("Passed"), :text("Grade received"), :text("You passed")'
    ).first.is_visible(timeout=500)
    if has_passed:
        return True
    if page.locator('[data-testid="TopBannerCTAButton"]').first.is_visible(timeout=500):
        return True
    has_eval = page.locator(':text("Grading in progress"), :text("Evaluating")').first.is_visible(timeout=300)
    has_disabled = page.locator('input[disabled], [aria-disabled="true"]').first.is_visible(timeout=300)
    has_active = page.locator('input:not([disabled]):not([type="hidden"])').first.is_visible(timeout=300)
    return bool(has_eval or (has_disabled and not has_active))
