"""File upload handling for peer-graded assignments via Uppy Dashboard."""

import logging
from pathlib import Path

from playwright.sync_api import Error, Page

logger = logging.getLogger(__name__)
ADD_BTN = 'button:has-text("Add File"), button:has(span.cds-button-label:has-text("Add File"))'
BROWSE_BTN = '.uppy-Dashboard-browse, button:has-text("browse files")'


def upload_peer_file(page: Page, file_path: Path) -> None:
    """Click Add File, trigger file chooser on Uppy, and upload target file."""
    if (btn := page.locator(ADD_BTN).first).is_visible(timeout=10000):
        logger.info("Clicking 'Add File' button...")
        btn.scroll_into_view_if_needed()
        btn.click()
        page.wait_for_timeout(2000)
    try:
        with page.expect_file_chooser(timeout=10000) as fc_info:
            page.locator(BROWSE_BTN).first.click(timeout=5000)
        fc_info.value.set_files(str(file_path))
    except Error:
        page.locator('input[type="file"]').first.set_input_files(str(file_path))
    logger.info("Attached submission file: %s", file_path.name)
    page.wait_for_timeout(2000)
