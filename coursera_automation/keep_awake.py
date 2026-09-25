"""System sleep prevention context manager for long automation runs."""

import ctypes
import logging
import os
import subprocess
import sys
from collections.abc import Generator
from contextlib import contextmanager, suppress

logger = logging.getLogger(__name__)

ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002
ES_AWAYMODE_REQUIRED = 0x00000040


def _set_windows_state(flags: int) -> None:
    """Invoke Windows kernel32 SetThreadExecutionState if available."""
    if hasattr(ctypes, "windll"):
        with suppress(AttributeError, OSError):
            ctypes.windll.kernel32.SetThreadExecutionState(flags)


@contextmanager
def keep_awake() -> Generator[None]:
    """Hold power assertion to prevent idle sleep across platforms."""
    proc: subprocess.Popen[bytes] | None = None
    if sys.platform == "darwin" and os.path.exists("/usr/bin/caffeinate"):
        with suppress(OSError):
            proc = subprocess.Popen(["/usr/bin/caffeinate", "-dims", "-w", str(os.getpid())])
            logger.info("Activated sleep prevention via caffeinate (PID: %d).", proc.pid)
    elif sys.platform == "win32":
        flags = ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED | ES_AWAYMODE_REQUIRED
        _set_windows_state(flags)
        logger.info("Activated sleep prevention via SetThreadExecutionState.")
    try:
        yield
    finally:
        if proc and proc.poll() is None:
            with suppress(OSError):
                proc.terminate()
                proc.wait(timeout=2)
            logger.info("Released sleep prevention power assertion.")
        elif sys.platform == "win32":
            _set_windows_state(ES_CONTINUOUS)
            logger.info("Released Windows execution state assertion.")

