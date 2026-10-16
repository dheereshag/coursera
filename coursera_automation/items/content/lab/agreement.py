"""Lab honor code agreement checkbox interaction."""

import logging
from contextlib import suppress

from playwright.sync_api import Error, Page, TimeoutError

logger = logging.getLogger(__name__)


def check_lab_agreement(page: Page) -> None:
    """Ensure Coursera Honor Code agreement checkbox is checked."""
    inp = page.locator('[aria-label="Coursera Honor Code"] input, input[value="agree"]').first
    lbl = page.locator('[aria-label="Coursera Honor Code"] label, label:has-text("agree")').first
    if inp.is_visible(timeout=300) or lbl.is_visible(timeout=300):
        target = lbl if lbl.is_visible(timeout=300) else inp
        with suppress(TimeoutError, Error):
            if not inp.is_checked(timeout=500):
                target.click(force=True)
                page.wait_for_timeout(300)
                if not inp.is_checked(timeout=500):
                    inp.check(force=True)
                logger.info("Checked lab agreement checkbox.")
                page.wait_for_timeout(2000)
