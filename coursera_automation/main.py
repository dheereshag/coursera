"""Entry point for parallel multi-instance Coursera automation."""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from playwright.sync_api import Error, sync_playwright
from playwright_stealth import Stealth

from coursera_automation.auth import login
from coursera_automation.course import open_course
from coursera_automation.instances import InstanceConfig, load_instances
from coursera_automation.items.navigation import register_dialog_handlers
from coursera_automation.keep_awake import keep_awake

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def run_instance(inst: InstanceConfig) -> None:
    """Execute complete automation workflow for a single instance."""
    cfg = inst.to_settings()
    name = f"{cfg.email.split('@')[0]}_{cfg.course_url.rstrip('/').split('/')[-1]}"
    logger.info("Starting automation for %s (%s)...", cfg.email, cfg.course_url)
    (user_dir := Path(f".browser_data/{name}")).mkdir(parents=True, exist_ok=True)
    for lk in user_dir.glob("Singleton*"):
        lk.unlink(missing_ok=True)
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(user_dir), headless=cfg.headless, viewport={"width": 1280, "height": 800},
            ignore_default_args=["--enable-automation"], args=["--disable-blink-features=AutomationControlled", "--disable-session-crashed-bubble"],
        )
        Stealth().apply_stealth_sync(context)
        page = context.pages[0] if context.pages else context.new_page()
        register_dialog_handlers(page)
        context.on("page", register_dialog_handlers)
        try:
            login(page, cfg); open_course(page, cfg); page.screenshot(path=f"coursera_{name}.png")
        finally:
            context.close()


def run(instances_path: str = "instances.py") -> None:
    """Load all configured instances and execute them in parallel."""
    instances = load_instances(instances_path)
    for inst in instances:
        inst.validate()
    logger.info("Executing %d automation instance(s) in parallel...", len(instances))
    with keep_awake(), ThreadPoolExecutor(max_workers=max(1, len(instances))) as ex:
        futs = [ex.submit(run_instance, inst) for inst in instances]
        for fut in as_completed(futs):
            try:
                fut.result()
            except (Error, OSError, RuntimeError, TimeoutError) as exc:
                logger.error("Automation instance failed: %s", exc)


if __name__ == "__main__":
    run()
