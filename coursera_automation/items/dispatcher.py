"""Item dispatcher: identifies item type and coordinates sequential execution."""

import logging
import re

from playwright.sync_api import Page

from coursera_automation.config import Settings
from coursera_automation.items.dialogue import handle_dialogue
from coursera_automation.items.discussion import handle_discussion
from coursera_automation.items.lab import handle_lab
from coursera_automation.items.navigator import click_next_item, dismiss_dialogs
from coursera_automation.items.quiz import handle_quiz
from coursera_automation.items.reading import handle_reading
from coursera_automation.items.video import handle_video

logger = logging.getLogger(__name__)


def dispatch_item(page: Page, cfg: Settings) -> None:
    """Detect current item type and execute corresponding handler."""
    dismiss_dialogs(page)
    is_reading = "/supplement" in page.url or page.locator(
        '[data-testid="mark-complete"], button:has-text("Mark as completed")'
    ).first.is_visible(timeout=1000)
    is_lab = any(k in page.url for k in ("/lab", "/ungradedLab", "/programming"))
    is_lab = is_lab or page.locator('button, a, [role="button"]').filter(
        has_text=re.compile(r"launch (app|lab)", re.IGNORECASE)
    ).first.is_visible(timeout=1500)

    if page.locator("video").first.is_visible(timeout=2000):
        handle_video(page, cfg)
    elif is_reading:
        handle_reading(page, cfg)
    elif is_lab:
        handle_lab(page, cfg)
    elif page.locator(
        'button:has-text("Start dialogue"), button:has-text("End dialogue"), button[aria-label="End Dialogue"]'
    ).first.is_visible(timeout=1000):
        handle_dialogue(page, cfg)
    elif page.locator('button:has-text("Reply")').first.is_visible(timeout=1000):
        handle_discussion(page, cfg)
    elif page.locator('button:has-text("assignment"), button:has-text("Try again")').first.is_visible(
        timeout=1000
    ):
        handle_quiz(page, cfg)
    else:
        handle_reading(page, cfg)


def process_items(page: Page, cfg: Settings) -> None:
    """Iterate through course items up to max_items limit."""
    for step in range(cfg.max_items):
        logger.info("Processing learning item %d of %d...", step + 1, cfg.max_items)
        dispatch_item(page, cfg)
        if not click_next_item(page, cfg):
            logger.info("Item sequence concluded.")
            break
