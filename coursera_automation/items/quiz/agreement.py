"""Coursera Honor Code checkbox agreement and legal name input handling."""

import logging
from contextlib import suppress

from playwright.sync_api import Error, Page

logger = logging.getLogger(__name__)

AGREE_SEL = (
    '#agreement-checkbox-base, '
    'label:has-text("understand and agree"), '
    '[data-testid="HonorCodeAgreement"] input[type="checkbox"]'
)
LEGAL_NAME_SEL = (
    'input[data-testid="honor-code-legal-name-input"], '
    'input[placeholder*="legal name" i], '
    '[data-testid="legal-name"] input'
)


def fill_honor_code(page: Page, legal_name: str = "", timeout_ms: int = 2000) -> None:
    """Check honor code agreement checkbox and fill legal name if present."""
    if (agree := page.locator(AGREE_SEL).first).is_visible(timeout=timeout_ms):
        with suppress(Error):
            agree.scroll_into_view_if_needed(timeout=1000)
            agree.click(force=True)
        logger.info("Checked Honor Code agreement checkbox.")
        page.wait_for_timeout(500)

    name_input = page.locator(LEGAL_NAME_SEL).first
    if name_input.is_visible(timeout=timeout_ms):
        if name_to_fill := legal_name.strip():
            with suppress(Error):
                name_input.scroll_into_view_if_needed(timeout=1000)
                name_input.fill(name_to_fill)
                logger.info("Filled Honor Code legal name: %s", name_to_fill)
        else:
            logger.warning("Honor Code legal name input is present, but no legal_name is configured.")
        page.wait_for_timeout(500)
