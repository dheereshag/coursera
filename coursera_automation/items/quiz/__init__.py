"""Quiz parsing, LLM solving, completion detection, and submission."""

from coursera_automation.items.quiz.coordinator import handle_quiz
from coursera_automation.items.quiz.launcher import (
    ensure_quiz_launched,
    is_on_cover_page,
)

__all__ = ["ensure_quiz_launched", "handle_quiz", "is_on_cover_page"]
