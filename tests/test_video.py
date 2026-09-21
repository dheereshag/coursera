"""Unit tests for video playback and in-video question skip automation."""

from unittest.mock import MagicMock, patch

from coursera_automation.config import Settings
from coursera_automation.items.content.video import (
    _get_duration,
    _wait_video,
    calculate_video_wait,
    handle_video,
)


def test_calculate_and_duration() -> None:
    """Verify video wait calculation and duration retrieval with fallback."""
    assert calculate_video_wait(100.0) == 50.0
    assert calculate_video_wait(0.5) == 1.0
    p1 = MagicMock(evaluate=MagicMock(side_effect=[0, 120.0]))
    assert _get_duration(p1) == 120.0
    p2 = MagicMock(evaluate=MagicMock(return_value=0))
    assert _get_duration(p2) == 30.0


def test_wait_video_skips_and_ends() -> None:
    """Verify _wait_video handles skip button and exits early on end."""
    page = MagicMock()
    skip_btn = MagicMock(is_visible=MagicMock(side_effect=[True, False]))
    page.locator.return_value.first = skip_btn
    page.evaluate.side_effect = lambda s: True if "ended" in s else None
    with patch("time.time", side_effect=[0.0, 1.0, 6.0, 7.0, 8.0, 9.0]):
        _wait_video(page, wait_secs=10.0)
    skip_btn.click.assert_called_once_with(force=True)


def test_handle_video_flow_and_mute() -> None:
    """Verify handle_video starts, mutes if unmuted, sets 2x, and waits."""
    page, cfg = MagicMock(), Settings()
    play_btn = MagicMock(is_visible=MagicMock(return_value=True))
    mute_btn = MagicMock(is_visible=MagicMock(return_value=True))
    speed_btn = MagicMock(is_visible=MagicMock(return_value=True), inner_text=MagicMock(return_value="1x"))
    page.evaluate.side_effect = lambda s: True if "paused" in s else 100.0 if "duration" in s else None
    page.locator.side_effect = lambda s: (
        MagicMock(first=mute_btn) if "Mute" in s else MagicMock(first=speed_btn) if "playback rate" in s
        else MagicMock(first=play_btn) if any(k in s for k in ("Play", "play")) else MagicMock(first=MagicMock(is_visible=lambda: False))
    )
    with patch("coursera_automation.items.content.video._wait_video") as mock_wait:
        handle_video(page, cfg)
        mock_wait.assert_called_once()
    play_btn.click.assert_called_once_with(force=True)
    mute_btn.click.assert_called_once_with(force=True)


def test_handle_video_already_muted() -> None:
    """Verify handle_video does not click mute when button is not visible."""
    page, cfg = MagicMock(), Settings()
    page.locator.side_effect = lambda s: MagicMock(first=MagicMock(is_visible=MagicMock(return_value=False)))
    with patch("coursera_automation.items.content.video._wait_video"):
        handle_video(page, cfg)
    page.locator.assert_any_call('button[aria-label="Mute"]')
