"""Unit tests for quiz interaction and question type detection."""

from unittest.mock import MagicMock, patch

from coursera_automation.config import Settings
from coursera_automation.items.quiz import handle_quiz
from coursera_automation.items.quiz.parser import _detect_type, _extract_prompt


def test_detect_type() -> None:
    """Verify _detect_type classifies textarea, multiselect, and single."""
    m1, m2, m3 = MagicMock(), MagicMock(), MagicMock()
    m1.locator.side_effect = lambda s: MagicMock(count=lambda: 2 if "checkbox" in s else 0)
    m2.locator.side_effect = lambda s: MagicMock(count=lambda: 0)
    m3.locator.side_effect = lambda s: MagicMock(count=lambda: 1 if "textarea" in s else 0)
    assert _detect_type(m1) == "multiselect" and _detect_type(m2) == "single" and _detect_type(m3) == "textarea"


def test_extract_prompt_cml() -> None:
    """Verify _extract_prompt retrieves prompt text from cml-viewer."""
    loc = MagicMock()
    loc.locator.return_value.first.inner_text.return_value = "What is AI?"
    assert _extract_prompt(loc) == "What is AI?"


def test_handle_quiz_flow() -> None:
    """Verify handle_quiz solves questions, checks agreement, and submits with modal."""
    page, cfg, agree, sub, modal = MagicMock(), Settings(), MagicMock(), MagicMock(), MagicMock()
    agree.is_visible = sub.is_visible = lambda *a, **kw: True
    modal.is_visible = MagicMock(side_effect=[True, False])
    q_loc = MagicMock(inner_text=lambda: "Q?", locator=lambda s: MagicMock(count=lambda: (0 if "agree" in s else 1), all=lambda: [MagicMock(inner_text=lambda: "4")], first=MagicMock(is_visible=lambda *a, **kw: False)))

    def loc_mock(s: str) -> MagicMock:
        if "agree" in s:
            return MagicMock(first=agree)
        if "dialog-submit-button" in s or "alertdialog" in s:
            return MagicMock(first=modal, last=modal)
        if "submit-button" in s:
            return MagicMock(first=sub)
        return MagicMock(all=lambda: [q_loc], first=MagicMock(is_visible=lambda *a, **kw: False))

    page.locator.side_effect = loc_mock
    with patch("coursera_automation.items.quiz.coordinator.solve_quiz_with_llm", return_value={0: ["4"]}), patch("coursera_automation.items.quiz.submit.poll_and_click_next", return_value=True):
        handle_quiz(page, cfg)
    assert agree.click.call_count == 1 and sub.click.call_count == 1 and modal.click.call_count == 1


def test_handle_quiz_fast_path() -> None:
    """Verify handle_quiz immediately advances when Next item CTA is already visible."""
    page, cfg = MagicMock(), Settings()
    page.locator.side_effect = lambda s: MagicMock(first=MagicMock(is_visible=lambda *a, **kw: ("TopBannerCTAButton" in s)))
    with patch("coursera_automation.items.quiz.coordinator.poll_and_click_next") as mock_poll:
        handle_quiz(page, cfg)
        mock_poll.assert_called_once_with(page, max_wait_sec=180)


def test_handle_quiz_empty_answers_aborts() -> None:
    """Verify handle_quiz aborts without submit when LLM returns empty answers."""
    page, cfg, agree = MagicMock(), Settings(), MagicMock()
    q_loc = MagicMock(locator=lambda s: MagicMock(count=lambda: 1))
    page.locator.side_effect = lambda s: MagicMock(first=agree) if "agree" in s else MagicMock(first=MagicMock(is_visible=lambda *a, **kw: False))
    with patch("coursera_automation.items.quiz.coordinator.wait_and_extract_questions", return_value=([q_loc], [{"text": "Q?"}])), patch("coursera_automation.items.quiz.coordinator.solve_quiz_with_llm", return_value={}), patch("coursera_automation.items.quiz.coordinator.submit_quiz") as mock_sub:
        handle_quiz(page, cfg)
        mock_sub.assert_not_called()
    agree.click.assert_not_called()


def test_handle_quiz_aborts_if_still_on_cover_page() -> None:
    """Verify handle_quiz aborts without extracting questions if still on cover page."""
    page, cfg = MagicMock(), Settings()
    page.locator.side_effect = lambda s: MagicMock(first=MagicMock(is_visible=lambda *a, **kw: ("CoverPageActionButton" in s)))
    with patch("coursera_automation.items.quiz.coordinator.ensure_quiz_launched"), patch(
        "coursera_automation.items.quiz.coordinator.wait_and_extract_questions"
    ) as mock_extract:
        handle_quiz(page, cfg)
        mock_extract.assert_not_called()


def test_handle_quiz_does_not_skip_when_active_questions_present() -> None:
    """Verify handle_quiz does not skip to next item if active questions are present."""
    page, cfg, agree, sub = MagicMock(), Settings(), MagicMock(), MagicMock()
    agree.is_visible = sub.is_visible = lambda *a, **kw: True
    q_loc = MagicMock(inner_text=lambda: "Q?", locator=lambda s: MagicMock(count=lambda: (0 if "agree" in s else 1), all=lambda: [MagicMock(inner_text=lambda: "Ans")], first=MagicMock(is_visible=lambda *a, **kw: False)))

    def loc_mock(s: str) -> MagicMock:
        if "CoverPageActionButton" in s:
            return MagicMock(first=MagicMock(is_visible=lambda *a, **kw: False), count=lambda: 0)
        if "agree" in s:
            return MagicMock(first=agree)
        if "Next item" in s:
            return MagicMock(first=MagicMock(is_visible=lambda *a, **kw: True))
        return MagicMock(all=lambda: [q_loc], first=MagicMock(is_visible=lambda *a, **kw: False), count=lambda: 1)

    page.locator.side_effect = loc_mock
    page.get_by_role.side_effect = lambda r, **kw: MagicMock(first=sub)
    with (
        patch("coursera_automation.items.quiz.coordinator.ensure_quiz_launched"),
        patch("coursera_automation.items.quiz.coordinator.wait_and_extract_questions", return_value=([q_loc], [{"index": 0, "type": "single", "question": "Q?", "options": ["Ans"]}])) as mock_extract,
        patch("coursera_automation.items.quiz.coordinator.solve_quiz_with_llm", return_value={0: ["Ans"]}) as mock_solve,
        patch("coursera_automation.items.quiz.coordinator.submit_quiz", return_value=True) as mock_sub,
    ):
        handle_quiz(page, cfg)
        mock_extract.assert_called_once()
        mock_solve.assert_called_once()
        mock_sub.assert_called_once()


def test_handle_quiz_proceeds_when_tunnel_vision_back_button_present() -> None:
    """Verify handle_quiz does not abort when tunnel-vision-back-button is visible."""
    page, cfg, agree, sub = MagicMock(), Settings(), MagicMock(), MagicMock()
    agree.is_visible = sub.is_visible = lambda *a, **kw: True
    q_loc = MagicMock(inner_text=lambda: "Q?", locator=lambda s: MagicMock(count=lambda: 1, all=lambda: [MagicMock(inner_text=lambda: "Ans")], first=MagicMock(is_visible=lambda *a, **kw: False)))

    def loc_mock(s: str) -> MagicMock:
        if "tunnel-vision-back-button" in s:
            return MagicMock(first=MagicMock(is_visible=lambda *a, **kw: True))
        if "CoverPageActionButton" in s:
            return MagicMock(first=MagicMock(is_visible=lambda *a, **kw: True), count=lambda: 1)
        if "agree" in s:
            return MagicMock(first=agree)
        return MagicMock(all=lambda: [q_loc], first=MagicMock(is_visible=lambda *a, **kw: False), count=lambda: 1)

    page.locator.side_effect = loc_mock
    page.get_by_role.side_effect = lambda r, **kw: MagicMock(first=sub)
    with (
        patch("coursera_automation.items.quiz.coordinator.ensure_quiz_launched"),
        patch("coursera_automation.items.quiz.coordinator.wait_and_extract_questions", return_value=([q_loc], [{"index": 0, "type": "single", "question": "Q?", "options": ["Ans"]}])) as mock_extract,
        patch("coursera_automation.items.quiz.coordinator.solve_quiz_with_llm", return_value={0: ["Ans"]}),
        patch("coursera_automation.items.quiz.coordinator.submit_quiz"),
    ):
        handle_quiz(page, cfg)
        mock_extract.assert_called_once()


