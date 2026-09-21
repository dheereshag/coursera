"""Unit tests for item calculation and logic."""

from unittest.mock import MagicMock, patch

from coursera_automation.config import Settings
from coursera_automation.items.dispatcher import dispatch_item
from coursera_automation.items.navigator import click_next_item, dismiss_dialogs
from coursera_automation.items.video import calculate_video_wait


def test_video_duration_exact() -> None:
    """Verify video wait calculation uses exact duration / 2.0 without ceiling."""
    assert calculate_video_wait(420.0) == 210.0
    assert calculate_video_wait(300.0) == 150.0
    assert calculate_video_wait(75.0) == 37.5
    assert calculate_video_wait(0.5) == 1.0


def test_dispatch_item_assignment() -> None:
    """Verify dispatch_item identifies assignment via .first and delegates to handle_quiz."""
    mock_page, cfg = MagicMock(), Settings()
    mock_page.url = "https://www.coursera.org/learn/example/lecture/abc"
    mock_page.locator.side_effect = lambda s: MagicMock(
        first=MagicMock(is_visible=MagicMock(return_value="assignment" in s)),
        filter=MagicMock(return_value=MagicMock(first=MagicMock(is_visible=MagicMock(return_value=False)))),
    )
    with (
        patch("coursera_automation.items.dispatcher.dismiss_dialogs"),
        patch("coursera_automation.items.dispatcher.handle_quiz") as mock_quiz,
    ):
        dispatch_item(mock_page, cfg)
        mock_quiz.assert_called_once_with(mock_page, cfg)


def test_dismiss_dialogs_honor_code() -> None:
    """Verify dismiss_dialogs clicks Continue on HonorCodeModal."""
    page, honor = MagicMock(), MagicMock()
    honor.first.is_visible.return_value = True
    btn = honor.first.locator.return_value.first
    btn.is_visible.return_value = True
    page.locator.side_effect = lambda s: honor if "HonorCodeModal" in s else MagicMock(first=MagicMock(is_visible=lambda timeout=0: False))
    dismiss_dialogs(page)
    btn.click.assert_called_once_with(force=True)


def test_click_next_item_top_banner() -> None:
    """Verify click_next_item clicks TopBannerCTAButton."""
    page, cfg, btn = MagicMock(), Settings(), MagicMock()
    btn.first.is_visible.return_value = True
    page.locator.side_effect = lambda s: btn if "TopBannerCTAButton" in s else MagicMock(first=MagicMock(is_visible=lambda timeout=0: False))
    with patch("coursera_automation.items.navigator.dismiss_dialogs"):
        assert click_next_item(page, cfg) is True
    btn.first.click.assert_called_once_with(force=True)

