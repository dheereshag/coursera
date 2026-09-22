"""Unit tests for quiz loader, progressive scrolling, and question count detection."""

from unittest.mock import MagicMock, patch

from coursera_automation.items.quiz.loader import (
    _detect_expected_count,
    load_and_stabilize_questions,
)


def test_detect_expected_count() -> None:
    page = MagicMock()
    page.locator.return_value.first.inner_text.return_value = "Assignment • 15 total questions"
    assert _detect_expected_count(page) == 15
    page.locator.return_value.first.inner_text.return_value = "Question 1 of 20"
    assert _detect_expected_count(page) == 20
    page.locator.return_value.first.inner_text.return_value = "Quiz"
    assert _detect_expected_count(page) == 0


def test_load_and_stabilize_questions_reaches_expected() -> None:
    page = MagicMock()
    page.locator.return_value.first.inner_text.return_value = "15 questions"
    loc_calls = [[MagicMock()] * 2, [MagicMock()] * 15]
    mock_find = MagicMock(side_effect=lambda p: loc_calls.pop(0) if loc_calls else [MagicMock()] * 15)
    with patch("coursera_automation.items.quiz.loader.dismiss_dialogs"):
        result = load_and_stabilize_questions(page, 5000, mock_find)
        assert len(result) == 15


def test_load_and_stabilize_questions_bottom_stabilization() -> None:
    page = MagicMock()
    page.locator.return_value.first.inner_text.return_value = "Quiz"
    page.locator.return_value.first.is_visible.return_value = True
    q_mock = [MagicMock()] * 5
    mock_find = MagicMock(return_value=q_mock)
    with patch("coursera_automation.items.quiz.loader.dismiss_dialogs"):
        result = load_and_stabilize_questions(page, 5000, mock_find)
        assert len(result) == 5
