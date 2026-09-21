"""Video playback automation: play, mute, 2x speed, duration wait."""

import logging
import time

from playwright.sync_api import Page

from coursera_automation.config import Settings

logger = logging.getLogger(__name__)


def calculate_video_wait(duration_seconds: float) -> float:
    """Calculate exact wait time in seconds at 2x speed: duration / 2.0."""
    return max(1.0, duration_seconds / 2.0)


def _get_duration(page: Page) -> float:
    """Wait for video metadata and return duration in seconds."""
    for _ in range(10):
        if (d := float(page.evaluate("() => document.querySelector('video')?.duration || 0"))) > 0:
            return d
        page.wait_for_timeout(500)
    return 30.0


def _wait_video(page: Page, wait_secs: float) -> None:
    """Poll video playback, click Skip on in-video questions, and wait."""
    skip = page.locator('button:has(span.cds-button-label:has-text("Skip")), button:has-text("Skip")').first
    end = time.time() + wait_secs
    while time.time() < end:
        if skip.is_visible(timeout=300):
            skip.click(force=True)
            page.wait_for_timeout(500)
            page.evaluate("() => document.querySelector('video')?.play()")
        if bool(page.evaluate("() => { const v = document.querySelector('video'); return v && v.ended && v.currentTime > 2.0; }")):
            break
        page.wait_for_timeout(1000)


def handle_video(page: Page, cfg: Settings) -> None:
    """Start video, reveal controls, mute, set 2x speed, and wait."""
    logger.info("Handling video item...")
    play_sel = '.vjs-big-play-button, .rc-VideoControlsContainer button, button[aria-label*="play" i], video'
    if (play := page.locator(play_sel).first).is_visible(timeout=cfg.timeout_ms):
        play.click(force=True)
        page.wait_for_timeout(500)
    if (mb := page.locator('button[aria-label="Mute"]').first).is_visible(timeout=2000):
        mb.click(force=True)
        logger.info("Muted video playback.")
    sb = page.locator('button[aria-label*="playback rate" i]').first
    if sb.is_visible(timeout=2000) and "2x" not in sb.inner_text().lower():
        for _ in range(4):
            sb.click(force=True)
            page.wait_for_timeout(300)
    page.evaluate("() => { const v = document.querySelector('video'); if (v) { v.playbackRate = 2.0; v.muted = true; v.play(); } }")
    wait_s = calculate_video_wait(dur := _get_duration(page))
    logger.info("Video duration: %.1fs. Waiting %.1fs at 2x...", dur, wait_s)
    _wait_video(page, wait_s)
    page.wait_for_timeout(6000)
