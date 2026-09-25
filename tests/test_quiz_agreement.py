"""Unit tests for Coursera Honor Code agreement checkbox and legal name input."""

from unittest.mock import MagicMock

from coursera_automation.items.quiz.agreement import (
    AGREE_SEL,
    LEGAL_NAME_SEL,
    fill_honor_code,
)


def test_fill_honor_code_full() -> None:
    """Verify fill_honor_code clicks agreement checkbox and fills legal name."""
    page = MagicMock()
    agree_btn = MagicMock(is_visible=MagicMock(return_value=True))
    name_input = MagicMock(is_visible=MagicMock(return_value=True))

    def loc_mock(sel: str) -> MagicMock:
        if sel == AGREE_SEL:
            return MagicMock(first=agree_btn)
        if sel == LEGAL_NAME_SEL:
            return MagicMock(first=name_input)
        return MagicMock(first=MagicMock(is_visible=MagicMock(return_value=False)))

    page.locator.side_effect = loc_mock
    fill_honor_code(page, legal_name="Palak Chandel")

    agree_btn.click.assert_called_once_with(force=True)
    name_input.fill.assert_called_once_with("Palak Chandel")


def test_fill_honor_code_checkbox_only() -> None:
    """Verify fill_honor_code functions when only agreement checkbox is present."""
    page = MagicMock()
    agree_btn = MagicMock(is_visible=MagicMock(return_value=True))
    name_input = MagicMock(is_visible=MagicMock(return_value=False))

    def loc_mock(sel: str) -> MagicMock:
        if sel == AGREE_SEL:
            return MagicMock(first=agree_btn)
        if sel == LEGAL_NAME_SEL:
            return MagicMock(first=name_input)
        return MagicMock(first=MagicMock(is_visible=MagicMock(return_value=False)))

    page.locator.side_effect = loc_mock
    fill_honor_code(page, legal_name="Palak Chandel")

    agree_btn.click.assert_called_once_with(force=True)
    name_input.fill.assert_not_called()


def test_fill_honor_code_empty_legal_name() -> None:
    """Verify fill_honor_code does not crash or fill when legal_name is blank."""
    page = MagicMock()
    agree_btn = MagicMock(is_visible=MagicMock(return_value=False))
    name_input = MagicMock(is_visible=MagicMock(return_value=True))

    def loc_mock(sel: str) -> MagicMock:
        if sel == AGREE_SEL:
            return MagicMock(first=agree_btn)
        if sel == LEGAL_NAME_SEL:
            return MagicMock(first=name_input)
        return MagicMock(first=MagicMock(is_visible=MagicMock(return_value=False)))

    page.locator.side_effect = loc_mock
    fill_honor_code(page, legal_name="   ")

    name_input.fill.assert_not_called()
