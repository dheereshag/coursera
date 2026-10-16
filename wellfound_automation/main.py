"""Main automation runner for Wellfound."""

import logging

from playwright.sync_api import Page

from wellfound_automation.auth import login_wellfound
from wellfound_automation.browser import launch_wellfound_context
from wellfound_automation.config import WellfoundConfig

logger = logging.getLogger(__name__)


def run(cfg: WellfoundConfig | None = None) -> bool:
    """Run the Wellfound login automation workflow."""
    config = cfg or WellfoundConfig()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    logger.info("Starting Wellfound automation for %s", config.email)
    with launch_wellfound_context(config) as context:
        page: Page = context.pages[0] if context.pages else context.new_page()
        return login_wellfound(page, config)


if __name__ == "__main__":
    run()
