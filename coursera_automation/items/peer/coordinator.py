"""Peer-graded assignment skipping and progression navigation."""

import logging

from playwright.sync_api import Page

from coursera_automation.config import Settings
from coursera_automation.items.navigation.dialogs import dismiss_dialogs
from coursera_automation.items.navigation.navigator import click_next_item

logger = logging.getLogger(__name__)


def handle_peer(page: Page, cfg: Settings) -> None:
    """Skip peer-graded assignment and advance to the next course item."""
    logger.info("Peer-graded assignment detected (%s). Skipping peer assignment as requested...", page.url)
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(3000)
    dismiss_dialogs(page)
    if not click_next_item(page, cfg):
        page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)
        click_next_item(page, cfg)
