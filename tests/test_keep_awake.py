"""Unit tests for keep_awake sleep prevention context manager."""

from unittest.mock import MagicMock, patch

from coursera_automation.keep_awake import keep_awake


def test_keep_awake_spawns_and_terminates() -> None:
    """Verify keep_awake launches caffeinate on macOS and terminates it on exit."""
    mock_proc = MagicMock()
    mock_proc.poll.return_value = None
    with (
        patch("sys.platform", "darwin"),
        patch("os.path.exists", return_value=True),
        patch("subprocess.Popen", return_value=mock_proc) as mock_popen,
    ):
        with keep_awake():
            mock_popen.assert_called_once()
        mock_proc.terminate.assert_called_once()
        mock_proc.wait.assert_called_once()


def test_keep_awake_non_darwin_noop() -> None:
    """Verify keep_awake is a safe no-op on non-macOS systems."""
    with patch("sys.platform", "linux"), patch("subprocess.Popen") as mock_popen:
        with keep_awake():
            pass
        mock_popen.assert_not_called()


def test_keep_awake_handles_os_error() -> None:
    """Verify keep_awake handles subprocess launch error gracefully."""
    with (
        patch("sys.platform", "darwin"),
        patch("os.path.exists", return_value=True),
        patch("subprocess.Popen", side_effect=OSError("Binary failed")),keep_awake()
    ):
        pass
