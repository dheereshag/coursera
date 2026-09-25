"""Specialization and course navigation steps."""

import logging
import re
import time

from playwright.sync_api import Error, Locator, Page

from coursera_automation.config import Settings
from coursera_automation.items.dispatcher import process_items
from coursera_automation.items.navigation import click_resume, dismiss_dialogs

logger = logging.getLogger(__name__)


def _wait_for_cta(page: Page, timeout_ms: int) -> Locator | None:
    cta = (
        page.get_by_role("link", name=re.compile(r"go to course", re.IGNORECASE))
        .or_(page.get_by_role("button", name=re.compile(r"go to course", re.IGNORECASE)))
        .or_(page.get_by_role("button", name=re.compile(r"enroll|join for free", re.IGNORECASE)))
        .first
    )
    res = page.locator('button, a, [role="button"]').filter(
        has=page.locator("span.cds-button-label", has_text=re.compile(r"resume", re.IGNORECASE))
    ).or_(page.locator('button, a, [role="button"]').filter(has_text=re.compile(r"resume|get started", re.IGNORECASE))).first
    deadline = time.monotonic() + (timeout_ms / 1000.0)
    while time.monotonic() < deadline:
        dismiss_dialogs(page)
        if any(k in str(page.url) for k in ("/lecture/", "/supplement/", "/exam/", "/quiz/", "/lab/", "/peer")):
            return None
        if cta.is_visible():
            return cta
        if res.is_visible():
            return None
        page.wait_for_timeout(1000)
    return None


def open_course(page: Page, cfg: Settings) -> None:
    """Navigate to specialization, click Go to course, resume, and process items."""
    course_url = getattr(cfg, "course_url", "")
    logger.info("Navigating to course page: %s", course_url)
    page.goto(course_url, wait_until="domcontentloaded")
    page.wait_for_timeout(2000)
    dismiss_dialogs(page)

    if cta := _wait_for_cta(page, max(cfg.timeout_ms, 40000)):
        logger.info("Clicking course CTA: %s", cta.inner_text().strip())
        try:
            cta.click(timeout=5000)
        except Error:
            dismiss_dialogs(page)
            cta.click(force=True)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(3000)
        dismiss_dialogs(page)
    else:
        logger.info("No 'Go to course' CTA visible; proceeding directly to Resume...")

    click_resume(page, cfg)
    process_items(page, cfg)
