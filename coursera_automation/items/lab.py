"""Lab automation handler: agree checkbox and launch app interaction."""

import logging
import re

from playwright.sync_api import Page

from coursera_automation.config import Settings
from coursera_automation.items.dialogs import dismiss_dialogs

logger = logging.getLogger(__name__)


def _check_agreement(page: Page) -> None:
    """Check agreement checkbox if present and unchecked."""
    agree = (
        page.get_by_label(re.compile(r"agree", re.IGNORECASE))
        .or_(page.locator('input[type="checkbox"]'))
        .first
    )
    if agree.is_visible(timeout=300) and not agree.is_checked():
        agree.check(force=True)
        logger.info("Checked 'I agree' checkbox.")
        page.wait_for_timeout(300)


def handle_lab(page: Page, cfg: Settings) -> None:
    """Scroll extensively, agree to terms, and launch lab application."""
    logger.info("Handling lab item...")
    page.wait_for_load_state("domcontentloaded")
    dismiss_dialogs(page)
    pat = re.compile(r"(launch|open|start) (app|lab|workspace)", re.IGNORECASE)
    launch = page.locator('button, a, [role="button"]').filter(has_text=pat).first
    for _ in range(16):
        _check_agreement(page)
        if launch.is_visible():
            break
        page.mouse.wheel(0, 800)
        page.wait_for_timeout(300)
    _check_agreement(page)
    if not launch.is_visible(timeout=1000):
        page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(500)
        _check_agreement(page)
    dismiss_dialogs(page)
    launch.wait_for(state="visible", timeout=cfg.timeout_ms)
    launch.scroll_into_view_if_needed()
    launch.click(force=True)
    logger.info("Clicked Launch App/Lab button. Keeping current tab in foreground...")
    page.wait_for_timeout(1000)
    page.bring_to_front()
    page.wait_for_timeout(2000)
