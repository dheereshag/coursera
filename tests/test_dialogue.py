"""Unit tests for dialogue automation and confirmation."""

from unittest.mock import MagicMock

from coursera_automation.config import Settings
from coursera_automation.items.interactive.dialogue import handle_dialogue


def test_handle_dialogue_with_text_chat() -> None:
    """Verify handle_dialogue clicks 'Use text chat' when present."""
    page, cfg = MagicMock(), Settings()
    btns = {k: MagicMock(is_visible=MagicMock(return_value=True)) for k in ("chat", "start", "end", "conf")}
    page.locator.side_effect = lambda s: (
        MagicMock(first=btns["chat"]) if "use-text-chat" in s
        else MagicMock(first=btns["start"]) if "Start" in s
        else MagicMock(first=btns["end"]) if "End" in s
        else MagicMock(first=btns["conf"])
    )
    handle_dialogue(page, cfg)
    for b in btns.values():
        b.click.assert_called_once()
    page.wait_for_timeout.assert_any_call(15000)


def test_handle_dialogue_already_started() -> None:
    """Verify handle_dialogue handles already started dialogue by clicking End."""
    page, cfg = MagicMock(), Settings()
    end_btn = MagicMock(is_visible=MagicMock(return_value=True))
    conf_btn = MagicMock(is_visible=MagicMock(return_value=True))
    page.locator.side_effect = lambda s: (
        MagicMock(first=MagicMock(is_visible=MagicMock(return_value=False))) if "Start" in s or "use-text-chat" in s
        else MagicMock(first=end_btn) if "End" in s
        else MagicMock(first=conf_btn)
    )
    handle_dialogue(page, cfg)
    end_btn.click.assert_called_once()
    conf_btn.click.assert_called_once()
    page.wait_for_timeout.assert_any_call(15000)


def test_handle_roleplay_end_and_confirm() -> None:
    """Verify handle_dialogue clicks 'End Role Play' and confirms in modal."""
    page, cfg = MagicMock(), Settings()
    end_btn = MagicMock(is_visible=MagicMock(return_value=True))
    conf_btn = MagicMock(is_visible=MagicMock(return_value=True))
    page.locator.side_effect = lambda s: (
        MagicMock(first=MagicMock(is_visible=MagicMock(return_value=False))) if "Start" in s or "use-text-chat" in s
        else MagicMock(first=end_btn) if "end-role-play" in s
        else MagicMock(first=conf_btn)
    )
    handle_dialogue(page, cfg)
    end_btn.click.assert_called_once()
    conf_btn.click.assert_called_once_with(force=True)
    page.wait_for_timeout.assert_any_call(15000)
