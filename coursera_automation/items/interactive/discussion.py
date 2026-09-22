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
        logger.info("Typed 'ok' into discussion chatbox.")
        page.wait_for_timeout(1000)

        reply_btn = page.get_by_role(
            "button", name=re.compile(r"^reply$", re.IGNORECASE)
        ).or_(page.get_by_text("Reply", exact=True)).first

        if reply_btn.is_visible(timeout=cfg.timeout_ms):
            reply_btn.click()
            logger.info("Clicked 'Reply' button. Waiting 12s for post to register...")
            page.wait_for_timeout(12000)


