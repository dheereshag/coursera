"""Video playback automation: play click, conditional 2x speed, exact duration wait."""

import logging
import time

from playwright.sync_api import Page

from coursera_automation.config import Settings

logger = logging.getLogger(__name__)


def calculate_video_wait(duration_seconds: float) -> float:
    """Calculate exact wait time in seconds at 2x speed: duration / 2.0."""
    return max(1.0, duration_seconds / 2.0)


def _wait_video(page: Page, wait_secs: float) -> None:
    """Poll video playback, click Skip on in-video questions, and wait."""
    skip = page.locator('button:has(span.cds-button-label:has-text("Skip")), button:has-text("Skip")').first
    end = time.time() + wait_secs
    while time.time() < end:
        if skip.is_visible(timeout=300):
            logger.info("In-video question detected. Clicking 'Skip'...")
            skip.click(force=True)
            page.wait_for_timeout(500)
            page.evaluate("() => document.querySelector('video')?.play()")
        if bool(page.evaluate("() => document.querySelector('video')?.ended")):
            break
        page.wait_for_timeout(1000)


def handle_video(page: Page, cfg: Settings) -> None:
    """Start video, reveal controls, set 2x speed if needed, and wait."""
    logger.info("Handling video item...")
    play = page.locator('.rc-VideoControlsContainer button, button[aria-label*="play" i]').first
    if play.is_visible(timeout=cfg.timeout_ms):
        play.click(force=True)
        page.wait_for_timeout(1000)

    page.evaluate("() => document.querySelector('video')?.play()")
    if (box := page.locator("video, .rc-VideoControlsContainer").first.bounding_box()):
        page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        page.wait_for_timeout(500)

    speed_btn = page.locator('button[aria-label*="playback rate" i]').first
    rate = float(page.evaluate("() => document.querySelector('video')?.playbackRate || 1"))
    is_2x = rate == 2.0 or (speed_btn.is_visible() and "2x" in speed_btn.inner_text().lower())
    if speed_btn.is_visible(timeout=3000) and not is_2x:
        for _ in range(4):
            speed_btn.click(force=True)
            page.wait_for_timeout(300)

    page.evaluate("() => { const v = document.querySelector('video'); if (v) { v.playbackRate = 2.0; v.play(); } }")
    dur = float(page.evaluate("() => document.querySelector('video')?.duration || 0"))
    wait_s = calculate_video_wait(dur) if dur > 0 else 30.0
    logger.info("Video duration: %.1fs. Waiting %.1fs at 2x...", dur, wait_s)
    _wait_video(page, wait_s)
    page.wait_for_timeout(6000)
