"""Unit tests for dialogue automation and confirmation."""

from unittest.mock import MagicMock

from coursera_automation.config import Settings
from coursera_automation.items.dialogue import handle_dialogue


def test_handle_dialogue_full_flow() -> None:
    """Verify handle_dialogue clicks start, end with aria-label, and confirms modal."""
    page, cfg = MagicMock(), Settings()
    start_btn = MagicMock(is_visible=MagicMock(return_value=True))
    end_btn = MagicMock(is_visible=MagicMock(return_value=True))
    confirm_btn = MagicMock(is_visible=MagicMock(return_value=True))

    page.locator.side_effect = lambda s: (
        MagicMock(first=start_btn) if "Start" in s
        else MagicMock(first=end_btn) if "End" in s
        else MagicMock(first=confirm_btn)
    )

    handle_dialogue(page, cfg)
    start_btn.click.assert_called_once()
    end_btn.click.assert_called_once()
    confirm_btn.click.assert_called_once()


def test_handle_dialogue_already_started() -> None:
    """Verify handle_dialogue handles already started dialogue by clicking End and confirming."""
    page, cfg = MagicMock(), Settings()
    end_btn = MagicMock(is_visible=MagicMock(return_value=True))
    confirm_btn = MagicMock(is_visible=MagicMock(return_value=True))

    page.locator.side_effect = lambda s: (
        MagicMock(first=MagicMock(is_visible=MagicMock(return_value=False))) if "Start" in s
        else MagicMock(first=end_btn) if "End" in s
        else MagicMock(first=confirm_btn)
    )

    handle_dialogue(page, cfg)
    end_btn.click.assert_called_once()
    confirm_btn.click.assert_called_once()
