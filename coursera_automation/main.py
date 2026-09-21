"""Entry point for single and multi-instance Coursera automation."""

import logging
from pathlib import Path

from playwright.sync_api import sync_playwright

from coursera_automation.auth import login
from coursera_automation.course import open_course
from coursera_automation.instances import InstanceConfig, load_instances
from coursera_automation.items.dialogs import register_dialog_handlers

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def run_instance(inst: InstanceConfig) -> None:
    """Execute complete automation workflow for a single instance."""
    cfg = inst.to_settings()
    logger.info("Starting automation for %s (%s)...", cfg.email, cfg.course_url)
    user_dir = Path(f".browser_data/{cfg.email.split('@')[0]}")
    user_dir.mkdir(parents=True, exist_ok=True)
    for lk in user_dir.glob("Singleton*"):
        try:
            lk.unlink(missing_ok=True)
        except OSError:
            pass
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(user_dir),
            headless=cfg.headless,
            viewport={"width": 1280, "height": 800},
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = context.pages[0] if context.pages else context.new_page()
        register_dialog_handlers(page)
        context.on("page", register_dialog_handlers)
        try:
            login(page, cfg)
            open_course(page, cfg)
            out_name = f"coursera_{cfg.email.split('@')[0]}.png"
            page.screenshot(path=out_name)
            logger.info("Saved final state to %s", out_name)
        finally:
            context.close()


def run(instances_path: str = "instances.json") -> None:
    """Load all configured instances and execute them."""
    instances = load_instances(instances_path)
    logger.info("Executing %d automation instance(s)...", len(instances))
    for idx, inst in enumerate(instances, 1):
        logger.info("--- Running instance %d/%d: %s ---", idx, len(instances), inst.email)
        run_instance(inst)


if __name__ == "__main__":
    run()
