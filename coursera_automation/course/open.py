"""Course opening and specialization navigation entrypoint."""

import logging

from playwright.sync_api import Error, Locator, Page

from coursera_automation.config import Settings
from coursera_automation.course.cta import wait_for_cta
from coursera_automation.items.dispatcher import process_items
from coursera_automation.items.navigation import click_resume, dismiss_dialogs

logger = logging.getLogger(__name__)


def _click_cta(page: Page, cta: Locator) -> None:
    logger.info("Clicking course CTA: %s", cta.inner_text().strip())
    try:
        cta.click(timeout=5000)
    except Error:
        dismiss_dialogs(page)
        cta.click(force=True)
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(3000)
    dismiss_dialogs(page)


def open_course(page: Page, cfg: Settings) -> None:
    """Navigate to specialization, click Go to course, resume, and process items."""
    course_url = getattr(cfg, "course_url", "")
    logger.info("Navigating to course page: %s", course_url)
    page.goto(course_url, wait_until="domcontentloaded")
    page.wait_for_timeout(2000)
    dismiss_dialogs(page)

    if cta := wait_for_cta(page, max(cfg.timeout_ms, 40000)):
        _click_cta(page, cta)
    else:
        logger.info("No 'Go to course' CTA visible; proceeding directly to Resume...")

    click_resume(page, cfg)
    process_items(page, cfg)
