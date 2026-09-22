"""Unit tests for quiz interaction and question type detection."""

from unittest.mock import MagicMock, patch

from coursera_automation.config import Settings
from coursera_automation.items.quiz import handle_quiz
from coursera_automation.items.quiz.parser import _detect_type, _extract_prompt


def test_detect_type() -> None:
    """Verify _detect_type returns multiselect for checkboxes, single otherwise."""
    m1, m2 = MagicMock(), MagicMock()
    m1.locator.return_value.count.return_value = 2
    m2.locator.return_value.count.return_value = 0
    assert _detect_type(m1) == "multiselect" and _detect_type(m2) == "single"


def test_extract_prompt_cml() -> None:
    """Verify _extract_prompt retrieves prompt text from cml-viewer."""
    loc = MagicMock()
    loc.locator.return_value.first.inner_text.return_value = "What is AI?"
    assert _extract_prompt(loc) == "What is AI?"


def test_handle_quiz_flow() -> None:
    """Verify handle_quiz solves questions, checks agreement, and submits with modal."""
    page, cfg, agree, sub, modal = MagicMock(), Settings(), MagicMock(), MagicMock(), MagicMock()
    agree.is_visible = sub.is_visible = modal.is_visible = lambda *a, **kw: True
    q_loc = MagicMock(inner_text=lambda: "Q?", locator=lambda s: MagicMock(count=lambda: (0 if "agree" in s else 1), all=lambda: [MagicMock(inner_text=lambda: "4")], first=MagicMock(is_visible=lambda *a, **kw: True)))
    page.locator.side_effect = lambda s: MagicMock(first=agree) if "agree" in s else (MagicMock(first=modal, last=modal) if any(k in s for k in ("cds-button", "dialog")) else MagicMock(all=lambda: [q_loc], first=MagicMock(is_visible=lambda *a, **kw: False)))
    page.get_by_role.side_effect = lambda r, **kw: MagicMock(first=sub) if "submit" in str(kw.get("name", "")).lower() else MagicMock(first=MagicMock(is_visible=lambda *a, **kw: False))
    with patch("coursera_automation.items.quiz.coordinator.solve_quiz_with_llm", return_value={0: ["4"]}), patch("coursera_automation.items.quiz.submit.poll_and_click_next"):
        handle_quiz(page, cfg)
    assert agree.click.call_count == 1 and sub.click.call_count == 1 and modal.click.call_count == 1


def test_handle_quiz_empty_answers_aborts() -> None:
    """Verify handle_quiz aborts without submit when LLM returns empty answers."""
    page, cfg, agree = MagicMock(), Settings(), MagicMock()
    q_loc = MagicMock(locator=lambda s: MagicMock(count=lambda: 1))
    page.locator.side_effect = lambda s: MagicMock(first=agree) if "agree" in s else MagicMock(first=MagicMock(is_visible=lambda *a, **kw: False))
    with patch("coursera_automation.items.quiz.coordinator.wait_and_extract_questions", return_value=([q_loc], [{"text": "Q?"}])), patch("coursera_automation.items.quiz.coordinator.solve_quiz_with_llm", return_value={}), patch("coursera_automation.items.quiz.coordinator.submit_quiz") as mock_sub:
        handle_quiz(page, cfg)
        mock_sub.assert_not_called()
    agree.click.assert_not_called()


def test_handle_quiz_empty_skips() -> None:
    """Verify handle_quiz skips LLM query and submission when 0 questions found."""
    page, cfg = MagicMock(), Settings()
    with patch("coursera_automation.items.quiz.coordinator.wait_and_extract_questions", return_value=([], [])), patch("coursera_automation.items.quiz.coordinator.solve_quiz_with_llm") as mock_solve, patch("coursera_automation.items.quiz.coordinator.submit_quiz") as mock_sub:
        handle_quiz(page, cfg)
        assert not mock_solve.called and not mock_sub.called
