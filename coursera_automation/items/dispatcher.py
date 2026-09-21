"""Item dispatcher: identifies item type and coordinates sequential execution."""

import logging

from playwright.sync_api import Page

from coursera_automation.config import Settings
from coursera_automation.items.content import handle_lab, handle_reading, handle_video
from coursera_automation.items.interactive import handle_dialogue, handle_discussion
from coursera_automation.items.navigation import click_next_item, dismiss_dialogs
from coursera_automation.items.quiz import handle_quiz

logger = logging.getLogger(__name__)


def dispatch_item(page: Page, cfg: Settings) -> None:
    """Detect current item type and execute corresponding handler."""
    dismiss_dialogs(page)
    dial = '[data-testid*="role-play"], [data-testid="use-text-chat-button"], button:has-text("Role Play"), button:has-text("dialogue")'
    is_vid = any(k in page.url for k in ("/lecture/", "/video/")) or page.locator(
        "video, .rc-VideoPlayer, [data-testid*='video']"
    ).first.is_visible(timeout=2500)
    is_lab = any(k in page.url for k in ("/lab/", "/ungradedLab/", "/programming/")) or page.locator(
        'form[data-testid="lti-launch-form"], [aria-label="Coursera Honor Code"], button:has-text("Launch App")'
    ).first.is_visible(timeout=1000)
    is_quiz = any(k in page.url for k in ("/exam/", "/quiz/", "/assignment")) or page.locator(
        '[data-testid="CoverPageActionButton"], button:has-text("Try again")'
    ).first.is_visible(timeout=2000)
    is_reading = "/supplement" in page.url or page.locator(
        '[data-testid="mark-complete"], button:has-text("Mark as completed")'
    ).first.is_visible(timeout=1000)

    if is_vid:
        handle_video(page, cfg)
    elif is_lab:
        handle_lab(page, cfg)
    elif is_quiz:
        handle_quiz(page, cfg)
    elif is_reading:
        handle_reading(page, cfg)
    elif any(k in page.url for k in ("/roleplay/", "/dialogue/")) or page.locator(dial).first.is_visible(timeout=1000):
        handle_dialogue(page, cfg)
    elif page.locator('button:has-text("Reply")').first.is_visible(timeout=1000):
        handle_discussion(page, cfg)
    else:
        handle_reading(page, cfg)


def process_items(page: Page, cfg: Settings) -> None:
    """Iterate through course items up to max_items limit."""
    for step in range(cfg.max_items):
        logger.info("Processing learning item %d of %d...", step + 1, cfg.max_items)
        dispatch_item(page, cfg)
        if not click_next_item(page, cfg):
            break
