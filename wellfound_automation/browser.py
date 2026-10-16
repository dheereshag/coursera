"""Browser lifecycle and persistent context management for Wellfound."""

import logging
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from playwright.sync_api import BrowserContext, sync_playwright
from playwright_stealth import Stealth

from wellfound_automation.config import WellfoundConfig

logger = logging.getLogger(__name__)


def prepare_user_data_dir(dir_path: str) -> str:
    """Ensure directory exists and clear any stale Chromium locks."""
    path = Path(dir_path)
    path.mkdir(parents=True, exist_ok=True)
    for lock in path.glob("Singleton*"):
        lock.unlink(missing_ok=True)
    return str(path)


@contextmanager
def launch_wellfound_context(
    cfg: WellfoundConfig,
) -> Generator[BrowserContext]:
    """Launch persistent browser context configured with stealth."""
    user_dir = prepare_user_data_dir(cfg.user_data_dir)
    args = [
        "--disable-blink-features=AutomationControlled",
        "--disable-session-crashed-bubble",
    ]
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_dir,
            headless=cfg.headless,
            viewport={"width": 1280, "height": 800},
            ignore_default_args=["--enable-automation"],
            args=args,
        )
        Stealth().apply_stealth_sync(context)
        try:
            yield context
        finally:
            context.close()
