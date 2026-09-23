"""Unit tests for quiz option normalization, index resolution, and clicking."""

from unittest.mock import MagicMock

from coursera_automation.items.quiz.option_matcher import (
    click_option,
    normalize_opt,
    resolve_option_index,
)


def test_normalize_opt_math_and_symbols() -> None:
    """Verify normalize_opt normalizes multiplication signs, punctuation, and math."""
    assert normalize_opt("500 * 0.10 * 40 * 12") == normalize_opt("500 × 0.10 × 40 × 12")
    assert normalize_opt("2,000 * 15 * 12 = 360,000") == normalize_opt("2{,}000 × 15 × 12 = 360{,}000")
    assert normalize_opt("$500 million") == normalize_opt("500 million")


def test_resolve_option_index_integer_and_letter() -> None:
    """Verify resolve_option_index handles integers and letters A-D."""
    opts = ["Option 1", "Option 2", "Option 3", "Option 4"]
    assert resolve_option_index(0, opts, 4) == 0
    assert resolve_option_index(2, opts, 4) == 2
    assert resolve_option_index(5, opts, 4) is None
    assert resolve_option_index("A", opts, 4) == 0
    assert resolve_option_index("b", opts, 4) == 1
    assert resolve_option_index("D", opts, 4) == 3


def test_resolve_option_index_math_katex() -> None:
    """Verify resolve_option_index matches KaTeX math expressions using normalization."""
    opts = [
        "500 × 0.10 × 40 × 12",
        "500 × 40 × 12",
        "500 × 0.10 × 40",
    ]
    assert resolve_option_index("500 * 0.10 * 40 * 12", opts, 3) == 0
    assert resolve_option_index("500 * 40 * 12", opts, 3) == 1


def test_resolve_option_index_verbatim_and_substring() -> None:
    """Verify resolve_option_index matches exact and substring text."""
    opts = [
        "A real-time dashboard that tracks a small set of key metrics",
        "A full-featured platform with custom dashboards",
    ]
    assert resolve_option_index("A real-time dashboard that tracks a small set of key metrics", opts, 2) == 0
    assert resolve_option_index("A real-time dashboard", opts, 2) == 0
    assert resolve_option_index("Nonexistent option", opts, 2) is None


def test_click_option_clicks_resolved_label() -> None:
    """Verify click_option resolves label by index and clicks it."""
    q_loc = MagicMock()
    label_0, label_1 = MagicMock(), MagicMock()
    label_0.locator.return_value.count.return_value = 0
    label_0.is_visible.return_value = True
    label_1.locator.return_value.count.return_value = 0
    label_1.is_visible.return_value = True

    labels_mock = MagicMock(count=lambda: 2)
    labels_mock.nth.side_effect = lambda i: [label_0, label_1][i]
    q_loc.locator.return_value = labels_mock

    opts = ["Alpha", "Beta"]
    click_option(q_loc, "Beta", opts)
    label_1.click.assert_called_once_with(force=True)
    label_0.click.assert_not_called()


def test_click_option_checks_checkbox_when_present() -> None:
    """Verify click_option calls check() if input[type=checkbox] is present."""
    q_loc = MagicMock()
    label = MagicMock()
    chk = MagicMock()
    label.locator.side_effect = lambda sel: MagicMock(count=lambda: 1 if "checkbox" in sel else 0, first=chk)
    label.is_visible.return_value = True

    labels_mock = MagicMock(count=lambda: 1)
    labels_mock.nth.return_value = label
    q_loc.locator.return_value = labels_mock

    click_option(q_loc, 0, ["First"])
    chk.check.assert_called_once_with(force=True)
    label.click.assert_not_called()


def test_click_option_fallback_filter_when_index_not_found() -> None:
    """Verify click_option falls back to text filter if option index resolution fails."""
    q_loc = MagicMock()
    fallback_btn = MagicMock(is_visible=lambda: True)
    fallback_btn.locator.return_value.count.return_value = 0

    labels_mock = MagicMock(count=lambda: 2)
    labels_mock.nth.return_value = MagicMock()
    labels_mock.filter.return_value = MagicMock(first=fallback_btn)
    q_loc.locator.return_value = labels_mock

    click_option(q_loc, "Unknown", ["Alpha", "Beta"])
    labels_mock.filter.assert_called_once_with(has_text="Unknown")
    fallback_btn.click.assert_called_once_with(force=True)
