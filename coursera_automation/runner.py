"""Single-instance browser automation runner for Coursera."""

import logging
from pathlib import Path

from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

from coursera_automation.auth import login
from coursera_automation.course import open_course
from coursera_automation.instances import InstanceConfig
from coursera_automation.items.navigation import register_dialog_handlers

logger = logging.getLogger(__name__)


def run_instance(inst: InstanceConfig) -> None:
    """Execute complete automation workflow for a single instance."""
    cfg = inst.to_settings()
    name = f"{cfg.email.split('@')[0]}_{cfg.course_url.rstrip('/').split('/')[-1]}"
    logger.info("Starting automation for %s (%s)...", cfg.email, cfg.course_url)

    user_dir = Path(f".browser_data/{name}")
    user_dir.mkdir(parents=True, exist_ok=True)
    for lock in user_dir.glob("Singleton*"):
        lock.unlink(missing_ok=True)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(user_dir),
            headless=cfg.headless,
            viewport={"width": 1280, "height": 800},
            ignore_default_args=["--enable-automation"],
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-session-crashed-bubble",
            ],
        )
        Stealth().apply_stealth_sync(context)
        page = context.pages[0] if context.pages else context.new_page()
        register_dialog_handlers(page)
        context.on("page", register_dialog_handlers)
        try:
            login(page, cfg)
            open_course(page, cfg)
            page.screenshot(path=f"coursera_{name}.png")
        finally:
            context.close()
