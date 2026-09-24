"""Unit tests for quiz retry CTA detection, clicking, fallback solving, and double-failure skip."""

from unittest.mock import MagicMock, call, patch

from coursera_automation.config import Settings
from coursera_automation.items.quiz.coordinator import handle_quiz
from coursera_automation.items.quiz.poll import poll_and_click_next
from coursera_automation.items.quiz.retry import click_retry, is_retry_available


def test_is_retry_available_true() -> None:
    """Verify is_retry_available returns True for visible enabled retry button."""
    page = MagicMock()
    btn = MagicMock(is_visible=MagicMock(return_value=True))
    btn.get_attribute.return_value = "false"
    btn.is_enabled.return_value = True
    page.locator.return_value.first = btn
    assert is_retry_available(page) is True


def test_is_retry_available_disabled_cooldown() -> None:
    """Verify is_retry_available returns False when button has aria-disabled='true'."""
    page = MagicMock()
    btn = MagicMock(is_visible=MagicMock(return_value=True))
    btn.get_attribute.return_value = "true"
    page.locator.return_value.first = btn
    assert is_retry_available(page) is False


def test_is_retry_available_not_visible() -> None:
    """Verify is_retry_available returns False when button is not visible."""
    page = MagicMock()
    btn = MagicMock(is_visible=MagicMock(return_value=False))
    page.locator.return_value.first = btn
    assert is_retry_available(page) is False


def test_click_retry_clicks_button_and_confirms_modal() -> None:
    """Verify click_retry clicks the button and confirms start attempt modal if visible."""
    page = MagicMock()
    retry_btn = MagicMock(is_visible=MagicMock(return_value=True))
    retry_btn.get_attribute.return_value = "false"
    modal_btn = MagicMock(is_visible=MagicMock(return_value=True))
    attempt_ready = MagicMock()

    def loc_mock(sel: str) -> MagicMock:
        if "StartAttemptModal" in sel:
            return MagicMock(first=modal_btn)
        if "part-" in sel or "tunnel-vision-back-button" in sel:
            return MagicMock(first=attempt_ready)
        return MagicMock(first=retry_btn)

    page.locator.side_effect = loc_mock
    assert click_retry(page) is True
    retry_btn.click.assert_called_once()
    modal_btn.click.assert_called_once()


def test_poll_and_click_next_clicks_retry_immediately() -> None:
    """Verify poll_and_click_next stops polling and clicks retry when Retry CTA is present."""
    page = MagicMock(url="https://coursera.org/learn/test/quiz/1")
    next_btn = MagicMock(is_visible=MagicMock(return_value=False))

    def loc_mock(sel: str) -> MagicMock:
        if "TopBannerCTAButton" in sel or "next-item" in sel:
            return MagicMock(first=next_btn)
        return MagicMock(first=MagicMock(is_visible=MagicMock(return_value=False)))

    page.locator.side_effect = loc_mock
    with (
        patch("coursera_automation.items.quiz.poll.is_retry_available", return_value=True),
        patch("coursera_automation.items.quiz.poll.click_retry") as mock_click_retry,
    ):
        result = poll_and_click_next(page, max_wait_sec=180)
        assert result is False
        mock_click_retry.assert_called_once_with(page)


def test_handle_quiz_retries_with_fallback_model_on_first_failure() -> None:
    """Verify handle_quiz tries primary model, then retries with fallback model when attempt 1 fails."""
    page, cfg = MagicMock(), Settings()
    with patch("coursera_automation.items.quiz.coordinator._run_attempt") as mock_attempt:
        # First attempt with primary fails, second attempt with fallback succeeds
        mock_attempt.side_effect = [False, True]
        handle_quiz(page, cfg)
        assert mock_attempt.call_args_list == [
            call(page, cfg, model=cfg.openrouter_model),
            call(page, cfg, model=cfg.openrouter_fallback_model),
        ]


def test_handle_quiz_double_failure_clicks_back_and_next() -> None:
    """Verify handle_quiz clicks back, waits 10s, and clicks next item when both attempts fail."""
    page, cfg = MagicMock(), Settings()
    back_btn = MagicMock()
    page.locator.return_value.first = back_btn

    with (
        patch("coursera_automation.items.quiz.coordinator._run_attempt", return_value=False),
        patch("coursera_automation.items.navigation.navigator.click_next_item") as mock_next,
    ):
        handle_quiz(page, cfg)
        back_btn.click.assert_called_once()
        page.wait_for_timeout.assert_called_with(10000)
        mock_next.assert_called_once_with(page, cfg)
