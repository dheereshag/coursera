"""Unit tests for keep_awake sleep prevention context manager."""

import os
from unittest.mock import MagicMock, patch

from coursera_automation.keep_awake import (
    ES_AWAYMODE_REQUIRED,
    ES_CONTINUOUS,
    ES_DISPLAY_REQUIRED,
    ES_SYSTEM_REQUIRED,
    keep_awake,
)


def test_keep_awake_spawns_and_terminates_macos() -> None:
    """Verify keep_awake launches caffeinate on macOS and terminates it on exit."""
    mock_proc = MagicMock()
    mock_proc.poll.return_value = None
    with (
        patch("sys.platform", "darwin"),
        patch("os.path.exists", return_value=True),
        patch("subprocess.Popen", return_value=mock_proc) as mock_popen,
        keep_awake(),
    ):
        mock_popen.assert_called_once_with(
            ["/usr/bin/caffeinate", "-dims", "-w", str(os.getpid())]
        )
    mock_proc.terminate.assert_called_once()
    mock_proc.wait.assert_called_once_with(timeout=2)


def test_keep_awake_windows() -> None:
    """Verify keep_awake invokes Win32 SetThreadExecutionState on Windows."""
    mock_kernel32 = MagicMock()
    mock_windll = MagicMock(kernel32=mock_kernel32)
    expected_flags = (
        ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED | ES_AWAYMODE_REQUIRED
    )
    with (
        patch("sys.platform", "win32"),
        patch("ctypes.windll", mock_windll, create=True),
        keep_awake(),
    ):
        mock_kernel32.SetThreadExecutionState.assert_called_once_with(expected_flags)
    assert mock_kernel32.SetThreadExecutionState.call_count == 2
    mock_kernel32.SetThreadExecutionState.assert_called_with(ES_CONTINUOUS)


def test_keep_awake_windows_without_windll() -> None:
    """Verify keep_awake handles Windows environments gracefully without windll."""
    with (
        patch("sys.platform", "win32"),
        patch("coursera_automation.keep_awake.hasattr", return_value=False),
        keep_awake(),
    ):
        pass


def test_keep_awake_linux_noop() -> None:
    """Verify keep_awake is a safe no-op on non-macOS/non-Windows systems."""
    with (
        patch("sys.platform", "linux"),
        patch("subprocess.Popen") as mock_popen,
        keep_awake(),
    ):
        pass
    mock_popen.assert_not_called()


def test_keep_awake_handles_os_error() -> None:
    """Verify keep_awake handles subprocess launch error gracefully."""
    with (
        patch("sys.platform", "darwin"),
        patch("os.path.exists", return_value=True),
        patch("subprocess.Popen", side_effect=OSError("Binary failed")),
        keep_awake(),
    ):
        pass
