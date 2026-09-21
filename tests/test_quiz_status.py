"""Unit tests for quiz completion detection."""

from unittest.mock import MagicMock, patch

from coursera_automation.config import Settings
from coursera_automation.items.quiz import handle_quiz
from coursera_automation.items.quiz.status import is_quiz_completed


def test_is_quiz_completed_under_review() -> None:
    """Verify is_quiz_completed returns False when submission is under review."""
    page = MagicMock()
    page.locator.side_effect = lambda s: MagicMock(
        first=MagicMock(is_visible=MagicMock(return_value="Reviewing" in s))
    )
    assert is_quiz_completed(page) is False


def test_is_quiz_completed_passed_and_cta() -> None:
    """Verify is_quiz_completed returns True when Passed or TopBannerCTAButton is present."""
    p1 = MagicMock(locator=lambda s: MagicMock(first=MagicMock(is_visible=lambda **kw: "Passed" in s)))
    assert is_quiz_completed(p1) is True
    p2 = MagicMock(locator=lambda s: MagicMock(first=MagicMock(is_visible=lambda **kw: "TopBanner" in s)))
    assert is_quiz_completed(p2) is True


def test_is_quiz_completed_false_when_retry() -> None:
    """Verify is_quiz_completed returns False when Try again button is visible."""
    page = MagicMock(locator=lambda s: MagicMock(first=MagicMock(is_visible=lambda **kw: "Try again" in s)))
    assert is_quiz_completed(page) is False


def test_is_quiz_completed_true_when_review_mode() -> None:
    """Verify is_quiz_completed returns True when inputs are disabled in review mode."""
    page = MagicMock()
    page.locator.side_effect = lambda s: MagicMock(
        first=MagicMock(is_visible=MagicMock(return_value="disabled" in s and "not([disabled])" not in s))
    )
    assert is_quiz_completed(page) is True


def test_handle_quiz_skips_when_completed() -> None:
    """Verify handle_quiz exits early without solver or submit when already completed."""
    page, cfg = MagicMock(), Settings()
    with (
        patch("coursera_automation.items.quiz.coordinator.is_quiz_completed", return_value=True),
        patch("coursera_automation.items.quiz.coordinator.solve_quiz_with_llm") as mock_solve,
        patch("coursera_automation.items.quiz.coordinator.submit_quiz") as mock_submit,
    ):
        handle_quiz(page, cfg)
        mock_solve.assert_not_called()
        mock_submit.assert_not_called()
