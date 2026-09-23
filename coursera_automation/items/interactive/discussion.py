"""Discussion prompt automation: type ok, dwell & scroll 60s, and advance."""

import logging
from contextlib import suppress

from playwright.sync_api import Error, Page

from coursera_automation.config import Settings

logger = logging.getLogger(__name__)
CHAT_SEL = 'div[data-slate-editor="true"][role="textbox"], div[role="textbox"][aria-label="Your Reply"], textarea, div[contenteditable="true"]'
REPLY_SEL = 'button[data-track-component="thread_reply"], button[id^="thread_reply_button"], button:has-text("Reply")'
NEXT_SEL = 'button:has-text("Go to next item"), button:has-text("Next item"), a:has-text("Next item")'


def handle_discussion(page: Page, cfg: Settings) -> None:
    """Type 'ok' into discussion prompt, submit Reply, dwell 60s, and advance."""
    logger.info("Handling discussion prompt item (7s load wait)...")
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(7000)

    chatbox = page.locator(CHAT_SEL).first
    if not chatbox.is_visible(timeout=2000) and (trig := page.locator('button:has-text("Reply"), button:has-text("Leave a response")').first).is_visible(timeout=4000):
        trig.scroll_into_view_if_needed()
        trig.click(force=True)
        page.wait_for_timeout(2000)

    if chatbox.is_visible(timeout=cfg.timeout_ms):
        chatbox.scroll_into_view_if_needed()
        chatbox.click()
        chatbox.press_sequentially("ok", delay=50)
        logger.info("Typed 'ok' into discussion chatbox. Waiting for Reply button to enable...")

        reply_btn = page.locator(REPLY_SEL).first
        for _ in range(10):
            if reply_btn.is_visible() and reply_btn.is_enabled() and reply_btn.get_attribute("aria-disabled") != "true":
                break
            page.wait_for_timeout(500)

        if reply_btn.is_visible(timeout=cfg.timeout_ms):
            logger.info("Reply button enabled. Waiting 5s before clicking...")
            page.wait_for_timeout(5000)
            reply_btn.click(force=True)
            logger.info("Clicked 'Reply'. Dwell & scroll for 60s for completion tick...")
            for s in range(12):
                page.mouse.wheel(0, 400)
                page.wait_for_timeout(5000)
                logger.info("Discussion dwell: %ds / 60s elapsed...", (s + 1) * 5)
            page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1000)

    next_btn = page.locator(NEXT_SEL).first
    if next_btn.is_visible(timeout=5000):
        with suppress(Error):
            next_btn.click(force=True)
            logger.info("Clicked 'Go to next item' on discussion prompt.")
            page.wait_for_timeout(3000)


