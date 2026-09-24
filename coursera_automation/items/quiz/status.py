"""Status and completion detection for Coursera quiz assignments."""

import logging

from playwright.sync_api import Error, Page, TimeoutError

logger = logging.getLogger(__name__)


def is_final_exam(page: Page) -> bool:
    """Check if current page is a Final Exam item."""
    try:
        hdr = page.locator('[data-testid="header-left"], header h1, [role="main"] h1').first
        return "final exam" in str(hdr.inner_text(timeout=300)).lower()
    except (Error, TimeoutError):
        return False


def is_quiz_completed(page: Page) -> bool:
    """Check if quiz is already passed or in review mode without retry."""
    if page.locator(':text("Reviewing your submission"), :text("hang tight")').first.is_visible(timeout=500):
        return False
    if page.locator('button:has-text("Try again"), button:has-text("Retry"), [data-testid="reload-icon"]').first.is_visible(timeout=500):
        return False
    if page.locator('[data-testid="CoverPageActionButton"], [data-e2e="CoverPageActionButton"], button:has-text("Resume assignment"), button:has-text("Resume")').first.is_visible():
        return False
    has_q = bool(page.locator('fieldset, [role="radiogroup"], .rc-Option, #agreement-checkbox-base').count())
    has_active = page.locator('input:not([disabled]):not([type="hidden"]), textarea:not([disabled])').first.is_visible(timeout=300)
    if has_q and (has_active or page.locator('#agreement-checkbox-base').first.is_visible(timeout=300)):
        return False
    has_back = page.locator('[data-testid="tunnel-vision-back-button"], button[aria-label="Back"]').first.is_visible(timeout=300)
    if has_back and page.locator('[data-testid="TopBannerCTAButton"]').first.is_visible(timeout=500):
        return True
    if has_back and (has_active or page.locator('button:has-text("Save draft")').first.is_visible(timeout=300)):
        return False
    if page.locator('button:has-text("Go to next item")').first.is_visible(timeout=500):
        return True
    has_passed = page.locator(
        ':text("Your grade:"), :text("Passed"), :text("Grade received"), :text("You passed")'
    ).first.is_visible(timeout=500)
    if has_passed and not page.locator('button:has-text("Start assignment")').first.is_visible():
        return True
    has_eval = page.locator(':text("Grading in progress"), :text("Evaluating")').first.is_visible(timeout=300)
    has_disabled = page.locator('input[disabled], [aria-disabled="true"]').first.is_visible(timeout=300)
    return bool(has_eval or (has_q and has_disabled and not has_active))
