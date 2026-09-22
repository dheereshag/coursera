"""Progressive scrolling and DOM hydration stabilization for quiz questions."""

import logging
import re
from collections.abc import Callable
from contextlib import suppress

from playwright.sync_api import Error, Locator, Page

from coursera_automation.items.navigation.dialogs import dismiss_dialogs

logger = logging.getLogger(__name__)
Q_SEL = 'fieldset, [role="radiogroup"], [role="group"], .rc-Option, [id^="prompt-autoGradableResponseId"], textarea'


def _detect_expected_count(page: Page) -> int:
    with suppress(Error, Exception):
        text = str(page.locator("header, [data-testid*='quiz'], [role='main']").first.inner_text())
        if m := re.search(r"(\d+)\s+(?:total\s+)?questions?|question\s+\d+\s+of\s+(\d+)", text, re.IGNORECASE):
            return int(m.group(1) or m.group(2))
    return 0


def load_and_stabilize_questions(page: Page, timeout_ms: int, find_fn: Callable[[Page], list[Locator]]) -> list[Locator]:
    """Scroll down through quiz attempt to hydrate all questions until count stabilizes."""
    with suppress(Error):
        page.locator(Q_SEL).first.wait_for(state="attached", timeout=timeout_ms)
    expected = _detect_expected_count(page)
    prev_count, stable_ticks = 0, 0
    for _ in range(20):
        page.mouse.wheel(0, 1000)
        page.wait_for_timeout(500)
        dismiss_dialogs(page)
        locs = find_fn(page)
        count = len(locs)
        if expected and count >= expected:
            logger.info("Reached expected %d questions.", expected)
            break
        bottom = page.locator('#agreement-checkbox-base, [data-testid*="submit"], button:has-text("Submit")').first.is_visible()
        if count > 0 and count == prev_count:
            stable_ticks += 1
            if stable_ticks >= 3 or (bottom and stable_ticks >= 2):
                logger.info("Question count stabilized at %d.", count)
                break
        else:
            stable_ticks = 0
        prev_count = count
    with suppress(Error):
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(500)
    return find_fn(page)
