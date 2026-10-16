"""Entry point for parallel multi-instance Coursera automation."""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from playwright.sync_api import Error

from coursera_automation.instances import load_instances
from coursera_automation.keep_awake import keep_awake
from coursera_automation.runner import run_instance

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


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
