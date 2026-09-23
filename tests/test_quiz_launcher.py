"""Unit tests for quiz attempt launcher, cover page CTA detection, and attempt modals."""

from unittest.mock import MagicMock, patch

from coursera_automation.items.quiz.launcher import (
    _find_cover_cta,
    ensure_quiz_launched,
    is_on_cover_page,
)


def test_ensure_quiz_launched_clicks_resume_cta() -> None:
    """Verify ensure_quiz_launched finds CoverPageActionButton, scrolls, and clicks it."""
    page = MagicMock()
    cta = MagicMock()
    cta.count.return_value = 1
    cta.is_visible.side_effect = lambda *a, **k: True
    cta.get_attribute.return_value = "false"
    cta.inner_text.return_value = "Resume assignment"

    modal = MagicMock()
    modal.is_visible.side_effect = lambda *a, **k: False

    attempt_ready = MagicMock()
    attempt_ready.is_visible.side_effect = lambda *a, **k: False

    def locator_mock(sel: str) -> MagicMock:
        if "CoverPageActionButton" in sel:
            return MagicMock(first=cta)
        if "StartAttemptModal" in sel:
            return MagicMock(first=modal)
        if "agreement-checkbox-base" in sel or "textarea" in sel:
            return MagicMock(first=attempt_ready)
        return MagicMock(first=MagicMock(is_visible=lambda *a, **k: False, count=lambda: 0))

    page.locator.side_effect = locator_mock

    with patch("coursera_automation.items.quiz.launcher.dismiss_dialogs"), patch(
        "coursera_automation.items.quiz.launcher.is_quiz_completed", return_value=False
    ):
        result = ensure_quiz_launched(page, timeout_ms=1000)

    assert result is True
    cta.scroll_into_view_if_needed.assert_called_once_with(timeout=1000)
    cta.click.assert_called_once_with(force=True, timeout=5000)
    attempt_ready.wait_for.assert_called_once_with(state="visible", timeout=8000)


def test_ensure_quiz_launched_confirms_attempt_modal() -> None:
    """Verify confirmation modal is clicked if it appears after launching attempt."""
    page = MagicMock()
    cta = MagicMock()
    cta.count.return_value = 1
    cta.is_visible.side_effect = lambda *a, **k: True
    cta.get_attribute.return_value = "false"
    cta.inner_text.return_value = "Start assignment"

    modal = MagicMock()
    modal.is_visible.side_effect = lambda *a, **k: True

    def locator_mock(sel: str) -> MagicMock:
        if "CoverPageActionButton" in sel:
            return MagicMock(first=cta)
        if "StartAttemptModal" in sel:
            return MagicMock(first=modal)
        return MagicMock(first=MagicMock(is_visible=lambda *a, **k: False, count=lambda: 0))

    page.locator.side_effect = locator_mock

    with patch("coursera_automation.items.quiz.launcher.dismiss_dialogs"), patch(
        "coursera_automation.items.quiz.launcher.is_quiz_completed", return_value=False
    ):
        result = ensure_quiz_launched(page, timeout_ms=1000)

    assert result is True
    cta.click.assert_called_once_with(force=True, timeout=5000)
    modal.click.assert_called_once_with(force=True)


def test_ensure_quiz_launched_skips_when_completed() -> None:
    """Verify ensure_quiz_launched returns False if quiz is already completed and no CTA exists."""
    page = MagicMock()
    page.locator.return_value.first.is_visible.side_effect = lambda *a, **k: False
    page.locator.return_value.first.count.return_value = 0
    with patch("coursera_automation.items.quiz.launcher.dismiss_dialogs"), patch(
        "coursera_automation.items.quiz.launcher.is_quiz_completed", return_value=True
    ):
        result = ensure_quiz_launched(page, timeout_ms=1000)

    assert result is False


def test_ensure_quiz_launched_prioritizes_cover_cta_over_completed_status() -> None:
    """Verify ensure_quiz_launched clicks Resume assignment even if is_quiz_completed would be True."""
    page = MagicMock()
    cta = MagicMock()
    cta.count.return_value = 1
    cta.is_visible.side_effect = lambda *a, **k: True
    cta.get_attribute.return_value = "false"
    cta.inner_text.return_value = "Resume assignment"

    page.locator.side_effect = lambda sel: MagicMock(
        first=cta if "CoverPageActionButton" in sel else MagicMock(is_visible=lambda *a, **k: False, count=lambda: 0)
    )

    with patch("coursera_automation.items.quiz.launcher.dismiss_dialogs"), patch(
        "coursera_automation.items.quiz.launcher.is_quiz_completed", return_value=True
    ):
        result = ensure_quiz_launched(page, timeout_ms=1000)

    assert result is True
    cta.click.assert_called_once_with(force=True, timeout=5000)


def test_ensure_quiz_launched_skips_when_attempt_ready() -> None:
    """Verify ensure_quiz_launched returns True if active attempt is already rendered, ignoring cover CTA."""
    page = MagicMock()
    cta = MagicMock(count=lambda: 1, is_visible=lambda *a, **k: True)
    attempt = MagicMock(is_visible=lambda *a, **k: True)

    def locator_mock(sel: str) -> MagicMock:
        if "agreement-checkbox-base" in sel or "textarea" in sel:
            return MagicMock(first=attempt)
        if "CoverPageActionButton" in sel:
            return MagicMock(first=cta)
        return MagicMock(first=MagicMock(is_visible=lambda *a, **k: False, count=lambda: 0))

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
    cta.is_visible.side_effect = lambda *a, **k: True
    cta.get_attribute.return_value = "true"

    page.locator.side_effect = lambda sel: MagicMock(
        first=cta if "CoverPageActionButton" in sel else MagicMock(is_visible=lambda *a, **k: False, count=lambda: 0)
    )

    with patch("coursera_automation.items.quiz.launcher.dismiss_dialogs"), patch(
        "coursera_automation.items.quiz.launcher.is_quiz_completed", return_value=False
    ):
        result = ensure_quiz_launched(page, timeout_ms=500)

    assert result is False
    cta.click.assert_not_called()


def test_is_on_cover_page() -> None:
    """Verify is_on_cover_page returns True only if CoverPageActionButton is visible and attempt is not ready."""
    page = MagicMock()
    cta = MagicMock()
    cta.count.return_value = 1
    cta.is_visible.return_value = True
    cta.inner_text.return_value = "Resume assignment"
    attempt_hidden = MagicMock()
    attempt_hidden.is_visible.return_value = False

    page.locator.side_effect = lambda sel: MagicMock(
        first=attempt_hidden if "agreement-checkbox-base" in sel else cta
    )
    assert is_on_cover_page(page) is True

    cta.is_visible.return_value = False
    assert is_on_cover_page(page) is False


def test_is_on_cover_page_false_when_attempt_ready() -> None:
    """Verify is_on_cover_page returns False when attempt is active even if CTA is in DOM."""
    page = MagicMock()
    cta = MagicMock(count=lambda: 1, is_visible=lambda *a, **k: True, inner_text=lambda: "Resume assignment")
    attempt_active = MagicMock(is_visible=lambda *a, **k: True)

    page.locator.side_effect = lambda sel: MagicMock(
        first=attempt_active if "agreement-checkbox-base" in sel or "textarea" in sel else cta
    )
    assert is_on_cover_page(page) is False
    assert _find_cover_cta(page) is None


def test_ensure_quiz_launched_ignores_weekly_learning_target_widget() -> None:
    """Verify weekly target widget with 'Not started' is ignored in favor of CoverPageActionButton."""
    page = MagicMock()
    target_widget = MagicMock(
        count=lambda: 1,
        is_visible=lambda *a, **k: True,
        inner_text=lambda: "Set up a weekly learning target\nSet up a weekly learning target, Not started",
    )
    cta = MagicMock(
        count=lambda: 1,
        is_visible=lambda *a, **k: True,
        get_attribute=lambda a: "false" if a == "aria-disabled" else None,
        inner_text=lambda: "Resume assignment",
    )

    def locator_mock(sel: str) -> MagicMock:
        if "CoverPageActionButton" in sel:
            return MagicMock(first=cta)
        if "target" in sel:
            return MagicMock(first=target_widget)
        return MagicMock(first=MagicMock(is_visible=lambda *a, **k: False, count=lambda: 0))

    page.locator.side_effect = locator_mock

    with patch("coursera_automation.items.quiz.launcher.dismiss_dialogs"), patch(
        "coursera_automation.items.quiz.launcher.is_quiz_completed", return_value=False
    ):
        result = ensure_quiz_launched(page, timeout_ms=1000)

    assert result is True
    cta.click.assert_called_once_with(force=True, timeout=5000)
    target_widget.click.assert_not_called()


def test_ensure_quiz_launched_clicks_try_again_cta() -> None:
    """Verify ensure_quiz_launched clicks Try again even when tunnel vision back button is visible."""
    page = MagicMock()
    try_again_btn = MagicMock(
        count=lambda: 1,
        is_visible=lambda *a, **k: True,
        get_attribute=lambda a: "false" if a == "aria-disabled" else None,
        inner_text=lambda: "Try again",
    )
    back_btn = MagicMock(is_visible=lambda *a, **k: True)

    def locator_mock(sel: str) -> MagicMock:
        if "Try again" in sel:
            return MagicMock(first=try_again_btn)
        if "tunnel-vision-back-button" in sel or "Back" in sel:
            return MagicMock(first=back_btn)
        return MagicMock(first=MagicMock(is_visible=lambda *a, **k: False, count=lambda: 0))

    page.locator.side_effect = locator_mock

    with patch("coursera_automation.items.quiz.launcher.dismiss_dialogs"), patch(
        "coursera_automation.items.quiz.launcher.is_quiz_completed", return_value=False
    ):
        result = ensure_quiz_launched(page, timeout_ms=1000)

    assert result is True
    try_again_btn.click.assert_called_once_with(force=True, timeout=5000)

