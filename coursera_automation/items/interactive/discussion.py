"""Discussion prompt automation: type ok and submit Reply."""

import logging
import re

from playwright.sync_api import Page

from coursera_automation.config import Settings

logger = logging.getLogger(__name__)


def handle_discussion(page: Page, cfg: Settings) -> None:
    """Type 'ok' into discussion prompt and click Reply."""
    logger.info("Handling discussion prompt item (10s load wait)...")
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(10000)

    chatbox = page.locator(
        'textarea, input[placeholder*="reply" i], div[contenteditable="true"], div[role="textbox"]'
    ).first
    if not chatbox.is_visible(timeout=2000):
        reply_trig = page.locator('button:has-text("Reply"), button:has-text("Leave a response")').first
        if reply_trig.is_visible(timeout=5000):
            reply_trig.scroll_into_view_if_needed()
            reply_trig.click()
            page.wait_for_timeout(2000)

    if chatbox.is_visible(timeout=cfg.timeout_ms):
        chatbox.scroll_into_view_if_needed()
        chatbox.fill("ok")
        logger.info("Typed 'ok' into discussion chatbox. Waiting 3s before clicking Reply...")
        page.wait_for_timeout(3000)

        reply_btn = page.get_by_role(
            "button", name=re.compile(r"^reply$", re.IGNORECASE)
        ).or_(page.get_by_text("Reply", exact=True)).first

        for _ in range(10):
            if reply_btn.is_visible() and reply_btn.is_enabled() and reply_btn.get_attribute("aria-disabled") != "true":
                break
            page.wait_for_timeout(500)

        if reply_btn.is_visible(timeout=cfg.timeout_ms):
            reply_btn.click(force=True)
            logger.info("Clicked 'Reply' button. Waiting 8s for next item to mount...")
            page.wait_for_timeout(8000)

        next_btn = page.locator('button:has-text("Go to next item"), button:has-text("Next item"), a:has-text("Next item")').first
        if next_btn.is_visible(timeout=5000):
            next_btn.click(force=True)
            logger.info("Clicked 'Go to next item' on discussion prompt.")
            page.wait_for_timeout(3000)


