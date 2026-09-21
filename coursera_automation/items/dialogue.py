"""Dialogue item automation: click Start dialogue and End dialogue."""

import logging

from playwright.sync_api import Page

from coursera_automation.config import Settings

logger = logging.getLogger(__name__)


def handle_dialogue(page: Page, cfg: Settings) -> None:
    """Handle dialogue/roleplay: Use text chat -> Start dialogue -> End dialogue."""
    logger.info("Handling dialogue item...")
    text_chat = page.locator(
        'button[data-testid="use-text-chat-button"], button:has-text("Use text chat")'
    ).first
    if text_chat.is_visible(timeout=2000):
        text_chat.click()
        logger.info("Clicked 'Use text chat' button.")
        page.wait_for_timeout(2000)

    start_btn = page.locator(
        'button:has(span.cds-button-label:has-text("Start Dialogue")), '
        'button:has-text("Start dialogue")'
    ).first
    if start_btn.is_visible(timeout=2000):
        start_btn.click()
        logger.info("Clicked 'Start dialogue'.")
        page.wait_for_timeout(2000)

    end_btn = page.locator(
        'button[aria-label="End Dialogue"], '
        'button:has(span.cds-button-label:has-text("End Dialogue")), '
        'button:has-text("End dialogue")'
    ).first
    if end_btn.is_visible(timeout=cfg.timeout_ms):
        end_btn.click()
        logger.info("Clicked 'End dialogue'.")
        page.wait_for_timeout(1500)

    confirm_sel = (
        'button:has(span.cds-button-label:has-text("Yes, end the Dialogue")), '
        'button:has-text("Yes, end the Dialogue"), '
        'button:has-text("Yes, end")'
    )
    confirm_btn = page.locator(confirm_sel).first
    if confirm_btn.is_visible(timeout=5000):
        confirm_btn.click(force=True)
        logger.info("Confirmed 'Yes, end the Dialogue' in modal.")
        page.wait_for_timeout(2500)

