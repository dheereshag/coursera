"""Unit tests for quiz attempt launcher, cover page CTA detection, and attempt modals."""

from unittest.mock import MagicMock, patch

from coursera_automation.items.quiz.launcher import (
    ensure_quiz_launched,
    is_on_cover_page,
)


def test_ensure_quiz_launched_clicks_resume_cta() -> None:
    """Verify ensure_quiz_launched finds CoverPageActionButton, scrolls, and clicks it."""
    page = MagicMock()
    cta = MagicMock()
    cta.count.return_value = 1
    cta.is_visible.return_value = True
    cta.get_attribute.return_value = "false"
    cta.inner_text.return_value = "Resume assignment"

    modal = MagicMock()
    modal.is_visible.return_value = False

    attempt_ready = MagicMock()
    attempt_ready.is_visible.return_value = False

    def locator_mock(sel: str) -> MagicMock:
        if "CoverPageActionButton" in sel:
            return MagicMock(first=cta)
        if "StartAttemptModal" in sel:
            return MagicMock(first=modal)
        if "agreement-checkbox-base" in sel:
            return MagicMock(first=attempt_ready)
        return MagicMock(first=MagicMock(is_visible=lambda: False, count=lambda: 0))

    page.locator.side_effect = locator_mock

    with patch("coursera_automation.items.quiz.launcher.dismiss_dialogs"), patch(
        "coursera_automation.items.quiz.launcher.is_quiz_completed", return_value=False
    ):
        result = ensure_quiz_launched(page, timeout_ms=1000)

    assert result is True
    cta.scroll_into_view_if_needed.assert_called_once_with(timeout=1000)
    cta.click.assert_called_once_with(force=True, timeout=5000)
    cta.wait_for.assert_called_once_with(state="hidden", timeout=8000)


def test_ensure_quiz_launched_confirms_attempt_modal() -> None:
    """Verify confirmation modal is clicked if it appears after launching attempt."""
    page = MagicMock()
    cta = MagicMock()
    cta.count.return_value = 1
    cta.is_visible.return_value = True
    cta.get_attribute.return_value = "false"
    cta.inner_text.return_value = "Start assignment"

    modal = MagicMock()
    modal.is_visible.return_value = True

    def locator_mock(sel: str) -> MagicMock:
        if "CoverPageActionButton" in sel:
            return MagicMock(first=cta)
        if "StartAttemptModal" in sel:
            return MagicMock(first=modal)
        return MagicMock(first=MagicMock(is_visible=lambda: False, count=lambda: 0))

    page.locator.side_effect = locator_mock

    with patch("coursera_automation.items.quiz.launcher.dismiss_dialogs"), patch(
        "coursera_automation.items.quiz.launcher.is_quiz_completed", return_value=False
    ):
        result = ensure_quiz_launched(page, timeout_ms=1000)

    assert result is True
    cta.click.assert_called_once_with(force=True, timeout=5000)
    modal.click.assert_called_once_with(force=True)


def test_ensure_quiz_launched_skips_when_completed() -> None:
    """Verify ensure_quiz_launched immediately returns False if quiz is already completed."""
    page = MagicMock()
    with patch("coursera_automation.items.quiz.launcher.dismiss_dialogs"), patch(
        "coursera_automation.items.quiz.launcher.is_quiz_completed", return_value=True
    ):
        result = ensure_quiz_launched(page, timeout_ms=1000)

    assert result is False
    page.locator.assert_not_called()


def test_ensure_quiz_launched_skips_when_attempt_ready() -> None:
    """Verify ensure_quiz_launched returns True if active attempt is already rendered."""
    page = MagicMock()
    cta = MagicMock(count=lambda: 0, is_visible=lambda: False)
    attempt = MagicMock(is_visible=lambda: True)

    def locator_mock(sel: str) -> MagicMock:
        if "CoverPageActionButton" in sel:
            return MagicMock(first=cta)
        if "agreement-checkbox-base" in sel:
            return MagicMock(first=attempt)
        return MagicMock(first=MagicMock(is_visible=lambda: False, count=lambda: 0))

    page.locator.side_effect = locator_mock

    with patch("coursera_automation.items.quiz.launcher.dismiss_dialogs"), patch(
        "coursera_automation.items.quiz.launcher.is_quiz_completed", return_value=False
    ):
        result = ensure_quiz_launched(page, timeout_ms=1000)

    assert result is True
    cta.click.assert_not_called()


def test_ensure_quiz_launched_ignores_disabled_button() -> None:
    """Verify ensure_quiz_launched does not click button if aria-disabled is true."""
    page = MagicMock()
    cta = MagicMock()
    cta.count.return_value = 1
    cta.is_visible.return_value = True
    cta.get_attribute.return_value = "true"

    page.locator.side_effect = lambda sel: MagicMock(first=cta if "CoverPageActionButton" in sel else MagicMock(is_visible=lambda: False, count=lambda: 0))

    with patch("coursera_automation.items.quiz.launcher.dismiss_dialogs"), patch(
        "coursera_automation.items.quiz.launcher.is_quiz_completed", return_value=False
    ):
        result = ensure_quiz_launched(page, timeout_ms=500)

    assert result is False
    cta.click.assert_not_called()


def test_is_on_cover_page() -> None:
    """Verify is_on_cover_page returns True if CoverPageActionButton is visible."""
    page = MagicMock()
    page.locator.return_value.first.is_visible.return_value = True
    assert is_on_cover_page(page) is True

    page.locator.return_value.first.is_visible.return_value = False
    assert is_on_cover_page(page) is False
