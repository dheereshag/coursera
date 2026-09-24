"""Quiz lifecycle: launch, solve, agree, submit, retry with fallback model."""

import logging
from contextlib import suppress

from playwright.sync_api import Error, Page

from coursera_automation.config import Settings

from .filler import fill_answers
from .launcher import ensure_quiz_launched, is_on_cover_page
from .parser import _is_textarea, wait_and_extract_questions
from .poll import BACK_BTN, poll_and_click_next
from .solver import solve_quiz_with_llm
from .status import is_quiz_completed
from .submit import submit_quiz

logger = logging.getLogger(__name__)


def _skip_failed_quiz(page: Page, cfg: Settings) -> None:
    from coursera_automation.items.navigation.navigator import click_next_item

    logger.warning("Quiz failed twice; clicking back, waiting 10s, and advancing to next item.")
    with suppress(Error):
        page.locator(BACK_BTN).first.click(timeout=3000)
    page.wait_for_timeout(10000)
    click_next_item(page, cfg)


def _run_attempt(page: Page, cfg: Settings, model: str) -> bool:
    ensure_quiz_launched(page, max(cfg.timeout_ms, 15000))
    if is_on_cover_page(page) and not page.locator(BACK_BTN).first.is_visible(timeout=500):
        return False
    if is_quiz_completed(page) or page.locator(':text("Reviewing your submission"), :text("hang tight")').first.is_visible():
        return poll_and_click_next(page, max_wait_sec=cfg.post_quiz_wait_sec)
    q_locs, questions = wait_and_extract_questions(page, cfg.timeout_ms)
    has_active = any(q.locator('input:not([disabled]), textarea:not([disabled]), [contenteditable="true"]').count() or _is_textarea(q) for q in q_locs)
    if not questions or not has_active:
        return poll_and_click_next(page, max_wait_sec=cfg.post_quiz_wait_sec)
    if not (answers := solve_quiz_with_llm(questions, cfg, model=model)):
        return False
    fill_answers(page, q_locs, questions, answers)
    if (agree := page.locator('#agreement-checkbox-base, label:has-text("understand and agree")').first).is_visible(timeout=cfg.timeout_ms):
        with suppress(Error):
            agree.scroll_into_view_if_needed(timeout=1000)
            agree.click(force=True)
        page.wait_for_timeout(1000)
    return submit_quiz(page, cfg)


def handle_quiz(page: Page, cfg: Settings) -> None:
    """Handle complete quiz lifecycle with primary and fallback models."""
    logger.info("Handling quiz with primary model (%s)...", cfg.openrouter_model)
    if _run_attempt(page, cfg, model=cfg.openrouter_model):
        return
    logger.warning("Attempt 1 did not pass. Retrying with fallback model (%s)...", cfg.openrouter_fallback_model)
    if _run_attempt(page, cfg, model=cfg.openrouter_fallback_model):
        return
    _skip_failed_quiz(page, cfg)
