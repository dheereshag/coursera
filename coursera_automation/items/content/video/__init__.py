"""Video content item subpackage."""

from coursera_automation.items.content.video.handler import handle_video
from coursera_automation.items.content.video.waiter import (
    calculate_video_wait,
    get_duration,
    wait_video,
)

_get_duration = get_duration
_wait_video = wait_video

__all__ = [
    "_get_duration",
    "_wait_video",
    "calculate_video_wait",
    "get_duration",
    "handle_video",
    "wait_video",
]
