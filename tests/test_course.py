"""Unit tests for course entry and dynamic CTA navigation."""

from unittest.mock import MagicMock, patch

from coursera_automation.config import Settings
from coursera_automation.course import _wait_for_cta, open_course


def test_wait_for_cta_found() -> None:
    page, cta = MagicMock(url="https://coursera.org/c"), MagicMock()
    cta.is_visible.return_value = True
    page.get_by_role.return_value.or_.return_value.or_.return_value.first = cta
    res = MagicMock(is_visible=lambda: False)
    page.locator.return_value.filter.return_value.or_.return_value.first = res
    with patch("coursera_automation.course.dismiss_dialogs"):
        assert _wait_for_cta(page, 2000) == cta


def test_wait_for_cta_bypasses_on_resume() -> None:
    page, cta = MagicMock(url="https://coursera.org/c"), MagicMock()
    cta.is_visible.return_value = False
    page.get_by_role.return_value.or_.return_value.or_.return_value.first = cta
    res = MagicMock(is_visible=lambda: True)
    page.locator.return_value.filter.return_value.or_.return_value.first = res
    with patch("coursera_automation.course.dismiss_dialogs"):
        assert _wait_for_cta(page, 2000) is None


def test_wait_for_cta_bypasses_on_item_url() -> None:
    page = MagicMock(url="https://coursera.org/learn/x/lecture/1")
    with patch("coursera_automation.course.dismiss_dialogs"):
        assert _wait_for_cta(page, 2000) is None


def test_open_course_clicks_cta() -> None:
    page, cfg, cta = MagicMock(), Settings(), MagicMock()
    cta.inner_text.return_value = "Go to Course"
    with (
        patch("coursera_automation.course._wait_for_cta", return_value=cta),
        patch("coursera_automation.course.dismiss_dialogs"),
        patch("coursera_automation.course.click_resume") as mock_resume,
        patch("coursera_automation.course.process_items") as mock_items,
    ):
        open_course(page, cfg)
        cta.click.assert_called_once_with(timeout=5000)
        mock_resume.assert_called_once_with(page, cfg)
        mock_items.assert_called_once_with(page, cfg)


def test_open_course_fallback_when_no_cta() -> None:
    page, cfg = MagicMock(), Settings()
    with (
        patch("coursera_automation.course._wait_for_cta", return_value=None),
        patch("coursera_automation.course.dismiss_dialogs"),
        patch("coursera_automation.course.click_resume") as mock_resume,
        patch("coursera_automation.course.process_items") as mock_items,
    ):
        open_course(page, cfg)
        mock_resume.assert_called_once_with(page, cfg)
        mock_items.assert_called_once_with(page, cfg)
