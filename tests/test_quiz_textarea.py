"""Unit tests for textarea question extraction and filling."""

from unittest.mock import MagicMock, patch

from coursera_automation.config import Settings
from coursera_automation.items.quiz.coordinator import handle_quiz
from coursera_automation.items.quiz.parser import (
    _detect_type,
    _extract_prompt,
    _find_textarea,
)


def test_extract_prompt_aria_labelledby() -> None:
    """Verify prompt is extracted via aria-labelledby referencing element."""
    loc = MagicMock()
    loc.locator.return_value.first.is_visible.return_value = False
    loc.get_attribute.side_effect = lambda a: "prompt-123" if a == "aria-labelledby" else None
    prompt_el = MagicMock(is_visible=MagicMock(return_value=True), inner_text=MagicMock(return_value="Explain CNN"))
    loc.page.locator.return_value.first = prompt_el
    assert _extract_prompt(loc) == "Explain CNN"


def test_extract_prompt_placeholder_fallback() -> None:
    """Verify prompt falls back to placeholder when cml and aria are missing."""
    loc = MagicMock()
    loc.locator.return_value.first.is_visible.return_value = False
    loc.get_attribute.side_effect = lambda a: "What do you think?" if a == "placeholder" else None
    loc.inner_text.return_value = ""
    assert _extract_prompt(loc) == "What do you think?"


def test_autogradable_prompt_and_find_textarea() -> None:
    """Verify prompt extraction and textarea discovery on autogradable prompt id."""
    loc, ta = MagicMock(), MagicMock()
    loc.evaluate.return_value = "DIV"
    loc.locator.side_effect = lambda s: MagicMock(count=lambda: 0, first=MagicMock(is_visible=lambda *a, **k: "cml" in s, inner_text=lambda: "Create prompt"))
    loc.get_attribute.side_effect = lambda a: "prompt-autoGradableResponseId~123" if a == "id" else None
    loc.page.locator.side_effect = lambda s: MagicMock(count=lambda: 1 if "prompt-autoGradableResponseId~123" in s else 0, first=ta)
    ta.is_visible.return_value = True
    assert _extract_prompt(loc) == "Create prompt" and _detect_type(loc) == "textarea" and _find_textarea(loc) == ta


def test_handle_quiz_fill_textarea() -> None:
    """Verify handle_quiz populates textarea with LLM response text."""
    page, cfg, ta, agree, sub = MagicMock(), Settings(), MagicMock(), MagicMock(), MagicMock()
    ta.is_visible.return_value = True
    page.locator.side_effect = lambda s: MagicMock(first=agree) if "agree" in s else MagicMock(first=MagicMock(is_visible=lambda *a, **kw: False))
    page.get_by_role.return_value.first = sub
    q_loc = MagicMock()
    q_loc.locator.side_effect = lambda s: MagicMock(first=ta, count=lambda: 1) if "textarea" in s else MagicMock(count=lambda: 0)

    with (
        patch("coursera_automation.items.quiz.coordinator.wait_and_extract_questions", return_value=([q_loc], [{"type": "textarea"}])),
        patch("coursera_automation.items.quiz.coordinator.solve_quiz_with_llm", return_value={0: ["My answer text"]}),
        patch("coursera_automation.items.quiz.coordinator.submit_quiz"),
    ):
        handle_quiz(page, cfg)
        ta.fill.assert_called_once_with("My answer text")
