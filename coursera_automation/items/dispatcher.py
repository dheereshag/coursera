"""Item dispatcher: identifies item type and coordinates sequential execution."""

import logging

from playwright.sync_api import Page

from coursera_automation.config import Settings
from coursera_automation.items.content import handle_lab, handle_reading, handle_video
from coursera_automation.items.interactive import handle_dialogue, handle_discussion
from coursera_automation.items.navigation import click_next_item, dismiss_dialogs
from coursera_automation.items.peer import handle_peer
from coursera_automation.items.quiz import handle_quiz

logger = logging.getLogger(__name__)


def dispatch_item(page: Page, cfg: Settings) -> None:
    """Detect current item type with 7s stabilization wait and execute handler."""
    logger.info("Stabilizing item page (7s load wait)...")
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(7000)
    dismiss_dialogs(page)

    url = page.url
    if any(k in url for k in ("/peer/", "/peer-assignment/")):
        handle_peer(page, cfg)
    elif any(k in url for k in ("/discussionPrompt/", "/discussion/", "/discussions/")):
        handle_discussion(page, cfg)
    elif any(k in url for k in ("/lecture/", "/video/")):
        handle_video(page, cfg)
    elif any(k in url for k in ("/lab/", "/ungradedLab/", "/ungradedLabWidget/", "/programming/")) :
        handle_lab(page, cfg)
    elif any(k in url for k in ("/exam/", "/quiz/", "/assignment")):
        handle_quiz(page, cfg)
    elif "/supplement" in url:
        handle_reading(page, cfg)
    elif page.locator('button[role="tab"]:has-text("My submission"), [data-track-page="peer_review_my_project"]').first.is_visible(timeout=5000):
        handle_peer(page, cfg)
    elif page.locator('button:has-text("Reply")').first.is_visible(timeout=5000):
        handle_discussion(page, cfg)
    elif page.locator("video, .rc-VideoPlayer, [data-testid*='video']").first.is_visible(timeout=3000):
        handle_video(page, cfg)
    elif page.locator('form[data-testid="lti-launch-form"], [aria-label="Coursera Honor Code"], button:has-text("Launch App"), button:has-text("Launch lab"), [data-track-component*="launch_lab"]').first.is_visible(timeout=3000):
        handle_lab(page, cfg)
    elif page.locator('[data-testid^="part-"], [data-testid="assignment-feedback-view"], [data-testid="tunnel-vision-back-button"], [data-testid="CoverPageActionButton"], button:has-text("Try again"), #agreement-checkbox-base').first.is_visible(timeout=3000):
        handle_quiz(page, cfg)
    elif page.locator('[data-testid*="role-play"], [data-testid="use-text-chat-button"], button:has-text("Role Play"), button:has-text("dialogue")').first.is_visible(timeout=3000):
        handle_dialogue(page, cfg)
    else:
        handle_reading(page, cfg)


def process_items(page: Page, cfg: Settings) -> None:
    """Iterate through course items up to max_items limit."""
    for step in range(cfg.max_items):
        orig_url = page.url
        dispatch_item(page, cfg)
        if page.url == orig_url and not click_next_item(page, cfg):
            break
