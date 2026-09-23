"""Unit tests for peer-graded assignment automation."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from coursera_automation.config import Settings
from coursera_automation.items.dispatcher import dispatch_item
from coursera_automation.items.peer.coordinator import handle_peer
from coursera_automation.items.peer.upload import upload_peer_file


def test_upload_peer_file() -> None:
    """Verify upload_peer_file clicks add and sets file via file chooser."""
    page = MagicMock()
    fc = MagicMock()
    page.expect_file_chooser.return_value.__enter__.return_value = MagicMock(value=fc)
    upload_peer_file(page, Path("test.png"))
    fc.set_files.assert_called_once()



@patch("coursera_automation.items.peer.coordinator.poll_and_click_next")
@patch("coursera_automation.items.peer.coordinator.upload_peer_file")
@patch("coursera_automation.items.peer.coordinator.dismiss_dialogs")
def test_handle_peer_flow(mock_dis: MagicMock, mock_up: MagicMock, mock_poll: MagicMock) -> None:
    """Verify handle_peer fills title, uploads, checks honor, and submits."""
    page, cfg = MagicMock(), Settings()
    sub_btn = MagicMock(is_visible=MagicMock(return_value=True), is_enabled=MagicMock(return_value=True))
    sub_btn.get_attribute.return_value = "false"
    modal_btn = MagicMock(is_visible=MagicMock(return_value=True))
    honor_btn = MagicMock(is_visible=MagicMock(return_value=True), is_checked=MagicMock(return_value=False))
    page.locator.side_effect = lambda s: (
        MagicMock(first=sub_btn) if "preview" in s else (
            MagicMock(first=modal_btn) if "dialog-submit-button" in s else (
                MagicMock(first=honor_btn) if "Honor Code" in s else MagicMock(first=MagicMock(is_visible=MagicMock(return_value=True)))
            )
        )
    )
    handle_peer(page, cfg)
    mock_up.assert_called_once()
    sub_btn.click.assert_called_once()
    modal_btn.click.assert_called_once()
    mock_poll.assert_called_once_with(page, max_wait_sec=180)


@patch("coursera_automation.items.dispatcher.dismiss_dialogs")
@patch("coursera_automation.items.dispatcher.handle_peer")
def test_dispatch_item_peer(mock_peer: MagicMock, mock_dis: MagicMock) -> None:
    """Verify dispatch_item detects peer URL and delegates to handle_peer."""
    page, cfg = MagicMock(url="https://coursera.org/learn/test/peer/123"), Settings()
    dispatch_item(page, cfg)
    mock_peer.assert_called_once_with(page, cfg)
