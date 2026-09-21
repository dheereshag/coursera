"""Unit tests for quiz completion detection."""

from unittest.mock import MagicMock, patch

from coursera_automation.config import Settings
from coursera_automation.items.quiz import handle_quiz
from coursera_automation.items.quiz_status import is_quiz_completed


def test_is_quiz_completed_true_when_passed_without_retry() -> None:
    """Verify is_quiz_completed returns True when Next item and Passed are present without Try again."""
    page = MagicMock()
    page.locator.side_effect = lambda s: MagicMock(
        first=MagicMock(is_visible=MagicMock(return_value="Try again" not in s))
    )
    assert is_quiz_completed(page) is True


def test_is_quiz_completed_false_when_retry_available() -> None:
    """Verify is_quiz_completed returns False when Try again button is visible."""
    page = MagicMock()
    page.locator.side_effect = lambda s: MagicMock(
        first=MagicMock(is_visible=MagicMock(return_value=True))
    )
    assert is_quiz_completed(page) is False


def test_is_quiz_completed_false_without_next() -> None:
    """Verify is_quiz_completed returns False when Next item button is absent."""
    page = MagicMock()
    page.locator.side_effect = lambda s: MagicMock(
        first=MagicMock(is_visible=MagicMock(return_value="Next item" not in s and "Try again" not in s))
    )
    assert is_quiz_completed(page) is False


def test_handle_quiz_skips_when_completed() -> None:
    """Verify handle_quiz exits early without solver or submit when already completed."""
    page, cfg = MagicMock(), Settings()
    with (
        patch("coursera_automation.items.quiz.is_quiz_completed", return_value=True),
        patch("coursera_automation.items.quiz.solve_quiz_with_llm") as mock_solve,
        patch("coursera_automation.items.quiz.submit_quiz") as mock_submit,
    ):
        handle_quiz(page, cfg)
        mock_solve.assert_not_called()
        mock_submit.assert_not_called()
