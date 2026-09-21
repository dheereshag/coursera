"""Unit tests for quiz submit and evaluation polling."""

from unittest.mock import MagicMock, patch

from coursera_automation.config import Settings
from coursera_automation.items.quiz.submit import _wait_for_evaluation, submit_quiz


def test_wait_for_evaluation_immediate_done() -> None:
    """Verify _wait_for_evaluation returns when Your grade is present and review done."""
    page = MagicMock()
    page.locator.side_effect = lambda s: MagicMock(
        first=MagicMock(is_visible=MagicMock(return_value="Reviewing" not in s))
    )
    _wait_for_evaluation(page, max_wait_sec=10)
    page.reload.assert_not_called()
    calls = [c[0][0] for c in page.locator.call_args_list]
    assert any(':text("Your grade:")' in s for s in calls)
    assert any(':text("Reviewing your submission")' in s for s in calls)


def test_wait_for_evaluation_reloads_when_pending() -> None:
    """Verify _wait_for_evaluation reloads page when review is pending."""
    page = MagicMock()
    page.locator.return_value.first.is_visible.side_effect = ([True, False] * 10) + [False, True]
    _wait_for_evaluation(page, max_wait_sec=60)
    page.reload.assert_called_once()


def test_submit_quiz_calls_evaluation_wait() -> None:
    """Verify submit_quiz clicks submit, confirms modal, and calls evaluation wait."""
    page, cfg = MagicMock(), Settings()
    sub_btn = MagicMock(is_visible=MagicMock(return_value=True))
    modal_btn = MagicMock(is_visible=MagicMock(return_value=True))
    page.get_by_role.return_value.first = sub_btn
    page.locator.return_value.first = modal_btn

    with patch("coursera_automation.items.quiz.submit._wait_for_evaluation") as mock_wait:
        submit_quiz(page, cfg)
        mock_wait.assert_called_once_with(page, max_wait_sec=300)
    sub_btn.click.assert_called_once()
    modal_btn.click.assert_called_once()
