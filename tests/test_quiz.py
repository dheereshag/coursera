"""Unit tests for quiz interaction and question type detection."""

from unittest.mock import MagicMock, patch

from coursera_automation.config import Settings
from coursera_automation.items.quiz import handle_quiz
from coursera_automation.items.quiz_parser import _detect_type, _extract_prompt


def test_detect_type() -> None:
    """Verify _detect_type returns multiselect for checkboxes, single otherwise."""
    mock_multi, mock_single = MagicMock(), MagicMock()
    mock_multi.locator.return_value.count.return_value = 2
    assert _detect_type(mock_multi) == "multiselect"
    mock_single.locator.return_value.count.return_value = 0
    assert _detect_type(mock_single) == "single"


def test_extract_prompt_cml() -> None:
    """Verify _extract_prompt retrieves prompt text from cml-viewer."""
    mock_loc, mock_cml = MagicMock(), MagicMock()
    mock_cml.first.is_visible.return_value = True
    mock_cml.first.inner_text.return_value = "What is AI?"
    mock_loc.locator.return_value = mock_cml
    assert _extract_prompt(mock_loc) == "What is AI?"


def test_handle_quiz_flow() -> None:
    """Verify handle_quiz solves questions, checks agreement, and submits with modal."""
    page, cfg = MagicMock(), Settings()
    q_loc, opt = MagicMock(), MagicMock()
    q_loc.inner_text.return_value, opt.inner_text.return_value = "What is 2+2?", "4"
    q_loc.locator.return_value.all.return_value, q_loc.locator.return_value.count.return_value = [opt], 0
    q_loc.locator.return_value.first.is_visible.return_value = False
    agree_mock, submit_mock, modal_sub_mock = MagicMock(is_visible=MagicMock(return_value=True)), MagicMock(is_visible=MagicMock(return_value=True)), MagicMock(is_visible=MagicMock(return_value=True))

    page.locator.side_effect = lambda s: MagicMock(first=agree_mock) if "understand and agree" in s else (
        MagicMock(first=modal_sub_mock, last=modal_sub_mock) if any(k in s for k in ("cds-button-label", "dialog-submit-button")) else MagicMock(all=lambda: [q_loc], first=MagicMock(is_visible=lambda timeout=0: False))
    )
    page.get_by_role.side_effect = lambda r, **kw: MagicMock(first=submit_mock) if "submit" in str(kw.get("name", "")).lower() else MagicMock(first=MagicMock(is_visible=lambda timeout=0: False))

    with patch("coursera_automation.items.quiz.solve_quiz_with_llm", return_value={0: ["4"]}):
        handle_quiz(page, cfg)

    agree_mock.click.assert_called_once_with(force=True)
    submit_mock.click.assert_called_once()
    modal_sub_mock.click.assert_called_once()


def test_handle_quiz_empty_skips() -> None:
    """Verify handle_quiz skips LLM query and submission when 0 questions found."""
    page, cfg = MagicMock(), Settings()
    with (
        patch("coursera_automation.items.quiz.wait_and_extract_questions", return_value=([], [])),
        patch("coursera_automation.items.quiz.solve_quiz_with_llm") as mock_solve,
        patch("coursera_automation.items.quiz.submit_quiz") as mock_submit,
    ):
        handle_quiz(page, cfg)
        mock_solve.assert_not_called()
        mock_submit.assert_not_called()
