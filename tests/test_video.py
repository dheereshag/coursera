"""Unit tests for video playback and in-video question skip automation."""

from unittest.mock import MagicMock, patch

from coursera_automation.config import Settings
from coursera_automation.items.video import (
    _wait_video,
    calculate_video_wait,
    handle_video,
)


def test_calculate_video_wait() -> None:
    """Verify video wait calculation uses duration / 2.0 with 1.0s floor."""
    assert calculate_video_wait(100.0) == 50.0
    assert calculate_video_wait(0.5) == 1.0


def test_wait_video_clicks_skip() -> None:
    """Verify _wait_video clicks Skip button when in-video question appears."""
    page = MagicMock()
    skip_btn = MagicMock(is_visible=MagicMock(side_effect=[True, False]))
    page.locator.return_value.first = skip_btn
    page.evaluate.side_effect = lambda script: True if "ended" in script else None

    _wait_video(page, wait_secs=5.0)
    skip_btn.click.assert_called_once_with(force=True)
    page.wait_for_timeout.assert_any_call(500)


def test_wait_video_breaks_when_ended() -> None:
    """Verify _wait_video exits early when video ends."""
    page = MagicMock()
    skip_btn = MagicMock(is_visible=MagicMock(return_value=False))
    page.locator.return_value.first = skip_btn
    page.evaluate.return_value = True

    _wait_video(page, wait_secs=10.0)
    skip_btn.click.assert_not_called()


def test_handle_video_full_flow() -> None:
    """Verify handle_video starts video, sets 2x speed, and calls _wait_video."""
    page, cfg = MagicMock(), Settings()
    play_btn = MagicMock(is_visible=MagicMock(return_value=True))
    speed_btn = MagicMock(is_visible=MagicMock(return_value=True), inner_text=MagicMock(return_value="1x"))
    page.locator.side_effect = lambda s: (
        MagicMock(first=speed_btn) if "playback rate" in s
        else MagicMock(first=play_btn) if "rc-VideoControlsContainer" in s
        else MagicMock(first=MagicMock(bounding_box=MagicMock(return_value=None)))
    )
    with patch("coursera_automation.items.video._wait_video") as mock_wait:
        handle_video(page, cfg)
        mock_wait.assert_called_once()
    play_btn.click.assert_called_once_with(force=True)
