"""Unit tests for multichoice (.rc-Option and role=group) quiz questions."""

from unittest.mock import MagicMock

from coursera_automation.items.quiz.parser import (
    _detect_type,
    _extract_prompt,
    _find_question_locs,
)


def test_find_question_locs_multichoice_group() -> None:
    """Verify _find_question_locs locates role=group and .rc-Option containers."""
    page, group_loc = MagicMock(), MagicMock()
    group_loc.locator.return_value.count.return_value = 0
    page.locator.side_effect = lambda s: MagicMock(all=lambda: [group_loc] if "group" in s else [])

    locs = _find_question_locs(page)
    assert locs == [group_loc]


def test_extract_options_and_prompt_multichoice() -> None:
    """Verify prompt and option extraction on multichoice question locator."""
    q_loc = MagicMock()
    q_loc.locator.side_effect = lambda s: MagicMock(
        count=lambda: 2 if "checkbox" in s else 0,
        first=MagicMock(is_visible=lambda *a, **k: "cml" in s, inner_text=lambda: "Choose appeals"),
        all=lambda: [MagicMock(inner_text=lambda: "Option A"), MagicMock(inner_text=lambda: "Option B")] if "label" in s else [],
    )
    assert _detect_type(q_loc) == "multiselect"
    assert _extract_prompt(q_loc) == "Choose appeals"
    options = [o.inner_text().strip() for o in q_loc.locator("label").all() if o.inner_text().strip()]
    assert options == ["Option A", "Option B"]
