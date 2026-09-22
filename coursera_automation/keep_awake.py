"""System sleep prevention context manager for long automation runs."""

import logging
import os
import subprocess
import sys
from collections.abc import Generator
from contextlib import contextmanager, suppress

logger = logging.getLogger(__name__)


@contextmanager
def keep_awake() -> Generator[None]:
    """Hold macOS caffeinate power assertion to prevent idle sleep."""
    proc: subprocess.Popen[bytes] | None = None
    if sys.platform == "darwin" and os.path.exists("/usr/bin/caffeinate"):
        try:
            proc = subprocess.Popen(["/usr/bin/caffeinate", "-dis", "-w", str(os.getpid())])
            logger.info("Activated sleep prevention via caffeinate (PID: %d).", proc.pid)
        except OSError as exc:
            logger.warning("Could not launch caffeinate: %s", exc)
    try:
        yield
    finally:
        if proc and proc.poll() is None:
            with suppress(OSError):
                proc.terminate()
                proc.wait(timeout=2)
            logger.info("Released sleep prevention power assertion.")
