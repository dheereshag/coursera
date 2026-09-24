"""Unit tests for peer-graded assignment automation."""

from unittest.mock import MagicMock, patch

from coursera_automation.config import Settings
from coursera_automation.items.dispatcher import dispatch_item
from coursera_automation.items.peer.coordinator import handle_peer


@patch("coursera_automation.items.peer.coordinator.click_next_item")
@patch("coursera_automation.items.peer.coordinator.dismiss_dialogs")
def test_handle_peer_skips_and_advances(mock_dis: MagicMock, mock_next: MagicMock) -> None:
    """Verify handle_peer dismisses dialogs and advances via click_next_item."""
    mock_next.return_value = True
    page, cfg = MagicMock(), Settings()
    handle_peer(page, cfg)
    mock_dis.assert_called_once_with(page)
    mock_next.assert_called_once_with(page, cfg)


@patch("coursera_automation.items.peer.coordinator.click_next_item")
@patch("coursera_automation.items.peer.coordinator.dismiss_dialogs")
def test_handle_peer_scrolls_fallback(mock_dis: MagicMock, mock_next: MagicMock) -> None:
    """Verify handle_peer scrolls to bottom and retries when first click fails."""
    mock_next.side_effect = [False, True]
    page, cfg = MagicMock(), Settings()
    handle_peer(page, cfg)
    page.evaluate.assert_called_once_with("() => window.scrollTo(0, document.body.scrollHeight)")
    assert mock_next.call_count == 2


@patch("coursera_automation.items.dispatcher.dismiss_dialogs")
@patch("coursera_automation.items.dispatcher.handle_peer")
def test_dispatch_item_peer_by_url(mock_peer: MagicMock, mock_dis: MagicMock) -> None:
    """Verify dispatch_item detects '/peer/' in URL and delegates to handle_peer."""
    page, cfg = MagicMock(url="https://coursera.org/learn/test/peer/123"), Settings()
    dispatch_item(page, cfg)
    mock_peer.assert_called_once_with(page, cfg)


@patch("coursera_automation.items.dispatcher.handle_reading")
@patch("coursera_automation.items.dispatcher.dismiss_dialogs")
@patch("coursera_automation.items.dispatcher.handle_peer")
def test_dispatch_item_ignores_peer_dom_without_url(
    mock_peer: MagicMock, mock_dis: MagicMock, mock_read: MagicMock
) -> None:
    """Verify dispatch_item does not trigger handle_peer without '/peer/' in URL."""
    page, cfg = MagicMock(url="https://coursera.org/learn/test/supplement/123"), Settings()
    dispatch_item(page, cfg)
    mock_peer.assert_not_called()
