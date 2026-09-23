"""Lab automation handler: agree checkbox and launch app interaction."""

import logging
import re
from contextlib import suppress

from playwright.sync_api import Error, Page, TimeoutError

from coursera_automation.config import Settings
from coursera_automation.items.navigation.dialogs import dismiss_dialogs

logger = logging.getLogger(__name__)
LAUNCH_SEL = 'button:has-text("Launch lab"), [data-track-component*="launch_lab"], button:has-text("Launch App")'


def _check_agreement(page: Page) -> None:
    """Ensure Coursera Honor Code agreement checkbox is checked."""
    inp = page.locator('[aria-label="Coursera Honor Code"] input, input[value="agree"]').first
    lbl = page.locator('[aria-label="Coursera Honor Code"] label, label:has-text("agree")').first
    if inp.is_visible(timeout=300) or lbl.is_visible(timeout=300):
        target = lbl if lbl.is_visible(timeout=300) else inp
        with suppress(TimeoutError, Error):
            if not inp.is_checked(timeout=500):
                target.click(force=True)
                page.wait_for_timeout(300)
                if not inp.is_checked(timeout=500): inp.check(force=True)
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
    _check_agreement(page)
    dismiss_dialogs(page)
    pat = re.compile(r"(launch|open|start) (app|lab|workspace)", re.IGNORECASE)
    btn = page.locator(LAUNCH_SEL).or_(page.locator('button, a, [role="button"]:not([disabled])').filter(has_text=pat)).first
    try:
        btn.wait_for(state="visible", timeout=10000)
        btn.scroll_into_view_if_needed()
        with page.expect_popup(timeout=6000) as pi:
            btn.click(force=True)
        pi.value.wait_for_load_state("domcontentloaded")
    except (TimeoutError, Error):
        with suppress(Error):
            if btn.is_visible(): btn.click(force=True)
    logger.info("Clicked launch button. Waiting 8s for lab component to mount...")
    page.wait_for_timeout(8000)
    page.bring_to_front()
    mark = page.locator('[data-testid="mark-complete"], button:has-text("Mark as completed")').first
    if mark.is_visible(timeout=3000) and ("completed" not in (t := mark.inner_text().lower()) or "mark" in t):
        mark.click(force=True)
        logger.info("Clicked 'Mark as completed' on lab.")
    page.wait_for_timeout(2000)
