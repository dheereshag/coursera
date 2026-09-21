"""Content and coursework automation handlers for Coursera."""

from coursera_automation.items.content.lab import handle_lab
from coursera_automation.items.content.reading import handle_reading
from coursera_automation.items.content.video import handle_video

__all__ = ["handle_lab", "handle_reading", "handle_video"]
