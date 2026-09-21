"""Specialization and course navigation steps."""

import logging
import re

from playwright.sync_api import Error, Page

from coursera_automation.config import Settings
from coursera_automation.items.dispatcher import process_items
from coursera_automation.items.navigation import click_resume, dismiss_dialogs

logger = logging.getLogger(__name__)


def open_course(page: Page, cfg: Settings) -> None:
    """Navigate to specialization, click Go to course, resume, and process items."""
    logger.info("Navigating to course page: %s", cfg.course_url)
    page.goto(cfg.course_url, wait_until="domcontentloaded")
    page.wait_for_timeout(2000)
    dismiss_dialogs(page)

    cta = (
        page.get_by_role("link", name=re.compile(r"go to course", re.IGNORECASE))
        .or_(page.get_by_role("button", name=re.compile(r"go to course", re.IGNORECASE)))
        .or_(page.get_by_role("button", name=re.compile(r"enroll", re.IGNORECASE)))
        .first
    )
    if cta.is_visible(timeout=5000):
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
