"""Dialogue and roleplay automation: text chat, start, end, and confirm."""

import logging

from playwright.sync_api import Page

from coursera_automation.config import Settings

logger = logging.getLogger(__name__)


def handle_dialogue(page: Page, cfg: Settings) -> None:
    """Handle dialogue/roleplay: Use text chat -> Start -> End -> Confirm modal."""
    logger.info("Handling dialogue / roleplay item...")
    text_chat = page.locator(
        'button[data-testid="use-text-chat-button"], button:has-text("Use text chat")'
    ).first
    if text_chat.is_visible(timeout=2000):
        text_chat.click()
        logger.info("Clicked 'Use text chat' button.")
        page.wait_for_timeout(2000)

    start_btn = page.locator(
        'button:has-text("Start Role Play"), button:has-text("Start Dialogue"), '
        'button:has-text("Start dialogue")'
    ).first
    if start_btn.is_visible(timeout=2000):
        start_btn.click()
        logger.info("Clicked start button.")
        page.wait_for_timeout(2000)

    end_btn = page.locator(
        'button[data-testid="end-role-play-button"], button:has-text("End Role Play"), '
        'button[aria-label*="End" i], button:has-text("End Dialogue"), button:has-text("End dialogue")'
    ).first
    if end_btn.is_visible(timeout=cfg.timeout_ms):
        end_btn.click()
        logger.info("Clicked 'End Role Play' / 'End dialogue'.")
        page.wait_for_timeout(2000)

    confirm_sel = (
        'button:has-text("Yes, end the Role Play"), '
        'button:has-text("Yes, end the Dialogue"), button:has-text("Yes, end")'
    )
    confirm_btn = page.locator(confirm_sel).first
    if confirm_btn.is_visible(timeout=5000):
        confirm_btn.click(force=True)
        logger.info("Confirmed ending in modal.")
        page.wait_for_timeout(2000)

    logger.info("Waiting 15s for dialogue finalization before advancing...")
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(15000)
