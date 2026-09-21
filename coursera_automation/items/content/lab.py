"""Lab automation handler: agree checkbox and launch app interaction."""

import logging
import re

from playwright.sync_api import Error, Page, TimeoutError

from coursera_automation.config import Settings
from coursera_automation.items.navigation.dialogs import dismiss_dialogs

logger = logging.getLogger(__name__)


def _check_agreement(page: Page) -> None:
    """Ensure Coursera Honor Code agreement checkbox is checked."""
    inp = page.locator('[aria-label="Coursera Honor Code"] input, input[value="agree"]').first
    lbl = page.locator('[aria-label="Coursera Honor Code"] label, label:has-text("agree")').first
    if (inp.is_visible(timeout=300) or lbl.is_visible(timeout=300)) and not inp.is_checked():
        (lbl if lbl.is_visible(timeout=300) else inp).click(force=True)
        page.wait_for_timeout(300)
        if not inp.is_checked():
            inp.check(force=True)
        logger.info("Checked lab agreement checkbox.")
        page.wait_for_timeout(2000)


def handle_lab(page: Page, cfg: Settings) -> None:
    """Scroll down, accept agreement, wait for Launch App, open tab, wait 10s."""
    logger.info("Handling lab item...")
    page.wait_for_load_state("domcontentloaded")
    dismiss_dialogs(page)
    for _ in range(4):
        page.mouse.wheel(0, 1000)
        page.wait_for_timeout(200)
    page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(500)
    _check_agreement(page)
    dismiss_dialogs(page)

    pat = re.compile(r"(launch|open|start) (app|lab|workspace)", re.IGNORECASE)
    btn = page.locator('button:has-text("Launch App"):not([disabled])').or_(
        page.locator('button, a, [role="button"]:not([disabled])').filter(has_text=pat)
    ).first
    try:
        btn.wait_for(state="visible", timeout=10000)
        with page.expect_popup(timeout=30000) as pi:
            btn.click(force=True)
        pi.value.wait_for_load_state("domcontentloaded")
    except (TimeoutError, Error):
        pass
    page.wait_for_timeout(10000)
    page.bring_to_front()

    mark = page.locator('[data-testid="mark-complete"], button:has-text("Mark as completed")').first
    if mark.is_visible(timeout=2000) and ("completed" not in (t := mark.inner_text().lower()) or "mark" in t):
        mark.click(force=True)
        logger.info("Clicked 'Mark as completed' on lab.")
    page.wait_for_timeout(2000)
