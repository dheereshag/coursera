"""Video playback duration and polling wait utilities."""

import logging
import time

from playwright.sync_api import Page

logger = logging.getLogger(__name__)

SKIP_SEL = 'button:has(span.cds-button-label:has-text("Skip")), button:has-text("Skip")'
PLAY_SEL = 'button[data-testid="playToggle"][aria-label="Play" i], button[aria-label="Play" i], .vjs-big-play-button'


def calculate_video_wait(duration_seconds: float) -> float:
    """Calculate exact wait time in seconds at 2x speed: duration / 2.0."""
    return max(1.0, duration_seconds / 2.0)


def get_duration(page: Page) -> float:
    """Wait for video metadata and return duration in seconds."""
    for _ in range(10):
        d = float(page.evaluate("() => document.querySelector('video')?.duration || 0") or 0)
        if d > 0:
            return d
        page.wait_for_timeout(500)
    return 30.0


def wait_video(page: Page, wait_secs: float) -> None:
    """Poll video playback every 0.5s, click Skip, click Play if paused, and wait."""
    skip, play = page.locator(SKIP_SEL).first, page.locator(PLAY_SEL).first
    start, end = time.time(), time.time() + wait_secs
    while time.time() < end:
        if skip.is_visible(timeout=100):
            skip.click(force=True)
            page.wait_for_timeout(300)
            page.evaluate("() => document.querySelector('video')?.play()")
        elif play.is_visible(timeout=100) and page.evaluate("() => document.querySelector('video')?.paused"):
            logger.info("Video paused; clicking Play button...")
            play.click(force=True)
            page.wait_for_timeout(300)
        if time.time() - start >= 5.0 and bool(page.evaluate("() => document.querySelector('video')?.ended")):
            break
        page.wait_for_timeout(500)
