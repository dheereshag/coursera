"""Course entry and resume progress navigation."""

import logging
import re

from playwright.sync_api import Page

from coursera_automation.config import Settings
from coursera_automation.items.navigation.dialogs import dismiss_dialogs

logger = logging.getLogger(__name__)


def click_resume(page: Page, cfg: Settings) -> None:
    """Scroll vertically and click Resume or Get started on course view."""
    if any(k in str(page.url) for k in ("/lecture/", "/supplement/", "/exam/", "/quiz/", "/lab/", "/peer")):
        return
    dismiss_dialogs(page)
    res = page.locator('button, a, [role="button"]').filter(has=page.locator("span.cds-button-label", has_text=re.compile(r"resume", re.IGNORECASE))).first
    start = page.locator('button, a, [role="button"]').filter(has_text=re.compile(r"get started", re.IGNORECASE)).first
    btn = None
    for _ in range(8):
        if (btn := next((b for b in (res, start) if b.is_visible()), None)):
            break
        page.mouse.wheel(0, 500)
        page.wait_for_timeout(400)
    btn = btn or res.or_(start).first
    btn.wait_for(state="visible", timeout=cfg.timeout_ms)
    btn.click(force=True)
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(10000)
    dismiss_dialogs(page)
