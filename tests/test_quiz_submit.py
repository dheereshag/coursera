"""Unit tests for quiz submit and post-submission next item polling."""

from unittest.mock import MagicMock, patch

from coursera_automation.config import Settings
from coursera_automation.items.quiz.poll import poll_and_click_next
from coursera_automation.items.quiz.submit import submit_quiz


def test_poll_and_click_next_immediate() -> None:
    """Verify poll_and_click_next clicks TopBannerCTAButton and advances."""
    page = MagicMock(url="https://coursera.org/learn/test/quiz/1")
    page.goto.side_effect = lambda url, **kw: setattr(page, "url", url)
    btn = MagicMock()
    btn.is_visible.return_value = True
    btn.get_attribute.return_value = "/learn/test/reading/2"
    page.locator.return_value.first = btn

    result = poll_and_click_next(page, max_wait_sec=10)
    assert result is True
    btn.click.assert_called_once()
    page.goto.assert_called_once_with("https://www.coursera.org/learn/test/reading/2", wait_until="domcontentloaded")


def test_poll_and_click_next_without_reload() -> None:
    """Verify poll_and_click_next waits without page reload while CTA is absent."""
    page = MagicMock(url="https://coursera.org/learn/test/quiz/1")
    btn = MagicMock()
    btn.is_visible.side_effect = [False] * 3 + [True]
    btn.get_attribute.return_value = None
    btn.click.side_effect = lambda **kw: setattr(page, "url", "https://coursera.org/learn/test/reading/2")
    inv = MagicMock(is_visible=MagicMock(return_value=False), count=MagicMock(return_value=0))
    page.locator.side_effect = lambda s: MagicMock(first=btn) if "next-item" in s or "TopBannerCTAButton" in s else MagicMock(first=inv)

    result = poll_and_click_next(page, max_wait_sec=25)
    assert result is True
    page.reload.assert_not_called()


def test_poll_and_click_next_timeout() -> None:
    """Verify poll_and_click_next returns False when CTA never appears."""
    page = MagicMock(url="https://coursera.org/learn/test/quiz/1")
    page.locator.return_value.first.is_visible.return_value = False
    assert poll_and_click_next(page, max_wait_sec=5) is False


def test_submit_quiz_calls_poll_and_click_next() -> None:
    """Verify submit_quiz clicks submit, confirms modal, waits, and calls poll_and_click_next."""
    page, cfg = MagicMock(), Settings()
    sub_btn = MagicMock(is_visible=MagicMock(return_value=True))
    modal_btn = MagicMock()
    modal_btn.is_visible.side_effect = [True, False]

    def loc_mock(sel: str) -> MagicMock:
        if "dialog-submit-button" in sel or "alertdialog" in sel:
            return MagicMock(first=modal_btn)
        return MagicMock(first=sub_btn)

    page.locator.side_effect = loc_mock

    with patch("coursera_automation.items.quiz.submit.poll_and_click_next") as mock_poll:
        submit_quiz(page, cfg)
        mock_poll.assert_called_once_with(page, max_wait_sec=180)
    sub_btn.click.assert_called_once()
    modal_btn.click.assert_called_once()
    assert page.wait_for_timeout.called


def test_poll_and_click_next_ignores_view_feedback() -> None:
    """Verify poll_and_click_next ignores view-feedback href and waits for next item."""
    page = MagicMock(url="https://coursera.org/learn/test/quiz/1")
    page.goto.side_effect = lambda url, **kw: setattr(page, "url", url)
    btn = MagicMock()
    btn.is_visible.return_value = True
    btn.get_attribute.side_effect = ["/learn/test/assignment/1/view-feedback", "/learn/test/supplement/10"]
    page.locator.return_value.first = btn

    result = poll_and_click_next(page, max_wait_sec=15)
    assert result is True
    btn.click.assert_called_once()
    page.goto.assert_called_once_with("https://www.coursera.org/learn/test/supplement/10", wait_until="domcontentloaded")


def test_submit_quiz_skips_poll_on_final_exam() -> None:
    """Verify submit_quiz skips poll_and_click_next when is_final_exam is True."""
    page, cfg = MagicMock(), Settings()
    sub_btn = MagicMock(is_visible=MagicMock(return_value=True))
    modal_btn = MagicMock(is_visible=MagicMock(return_value=False))

    def loc_mock(sel: str) -> MagicMock:
        if "dialog" in sel or "alertdialog" in sel:
            return MagicMock(first=modal_btn)
        return MagicMock(first=sub_btn)

    page.locator.side_effect = loc_mock

    with (
        patch("coursera_automation.items.quiz.submit.is_final_exam", return_value=True),
        patch("coursera_automation.items.quiz.submit.poll_and_click_next") as mock_poll,
    ):
        submit_quiz(page, cfg)
        mock_poll.assert_not_called()


def test_poll_and_click_next_skips_on_final_exam() -> None:
    """Verify poll_and_click_next returns False immediately when is_final_exam is True."""
    page = MagicMock()
    with patch("coursera_automation.items.quiz.poll.is_final_exam", return_value=True):
        assert poll_and_click_next(page) is False


def test_modal_btn_does_not_match_page_submit_controls() -> None:
    """Verify MODAL_BTN never targets in-page AttemptViewSubmitControls buttons."""
    from coursera_automation.items.quiz.submit import MODAL_BTN, SUB_SEL
    assert "AttemptViewSubmitControls" not in MODAL_BTN
    assert "dialog-submit-button" in MODAL_BTN
    assert "submit-button" in SUB_SEL



