"""Dialogue item automation: click Start dialogue and End dialogue."""

import logging

from playwright.sync_api import Page

from coursera_automation.config import Settings

logger = logging.getLogger(__name__)


def handle_dialogue(page: Page, cfg: Settings) -> None:
    """Handle dialogue item: Start dialogue -> End dialogue."""
    logger.info("Handling dialogue item...")
    start_btn = page.locator(
        'button:has(span.cds-button-label:has-text("Start Dialogue")), '
        'button:has-text("Start dialogue")'
    ).first
    if start_btn.is_visible(timeout=cfg.timeout_ms):
        start_btn.click()
        logger.info("Clicked 'Start dialogue'.")
        page.wait_for_timeout(2000)

    end_btn = page.locator(
        'button:has(span.cds-button-label:has-text("End Dialogue")), '
        'button:has-text("End dialogue")'
    ).first
    if end_btn.is_visible(timeout=cfg.timeout_ms):
        end_btn.click()
        logger.info("Clicked 'End dialogue'.")
        page.wait_for_timeout(2000)

