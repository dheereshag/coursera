"""Video playback automation handler."""

import logging

from playwright.sync_api import Page

from coursera_automation.config import Settings
from coursera_automation.items.content.video.waiter import (
    PLAY_SEL,
    calculate_video_wait,
    get_duration,
    wait_video,
)

logger = logging.getLogger(__name__)


def _start_and_configure_player(page: Page, timeout_ms: int) -> None:
    play = page.locator(PLAY_SEL).first
    is_paused = page.evaluate(
        "() => !document.querySelector('video') || document.querySelector('video').paused"
    )
    if is_paused and play.is_visible(timeout=timeout_ms):
        play.click(force=True)
        page.wait_for_timeout(500)
    for sel in ('button[aria-label="Mute"]', 'button[aria-label*="playback rate" i]'):
        if (b := page.locator(sel).first).is_visible(timeout=2000):
            b.click(force=True)
    page.evaluate(
        "() => { const v = document.querySelector('video'); if (v) { v.playbackRate = 2.0; v.muted = true; v.play(); } }"
    )


def handle_video(page: Page, cfg: Settings) -> None:
    """Start video, reveal controls, mute, set 2x speed, and wait."""
    logger.info("Handling video item...")
    _start_and_configure_player(page, cfg.timeout_ms)
    dur = get_duration(page)
    logger.info("Video duration: %.1fs. Waiting at 2x...", dur)
    wait_video(page, calculate_video_wait(dur))
    page.wait_for_timeout(6000)
