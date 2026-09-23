"""Quiz lifecycle: launch, solve, fill answers, agree, and submit."""

import logging
from contextlib import suppress

from playwright.sync_api import Error, Page

from coursera_automation.config import Settings

from .launcher import ensure_quiz_launched, is_on_cover_page
from .option_matcher import click_option
from .parser import _find_textarea, _is_textarea, wait_and_extract_questions
from .solver import solve_quiz_with_llm
from .status import is_quiz_completed
from .submit import poll_and_click_next, submit_quiz

logger = logging.getLogger(__name__)


def handle_quiz(page: Page, cfg: Settings) -> None:
    """Handle complete quiz lifecycle: launch, solve, agree, and submit."""
    logger.info("Handling quiz assignment...")
    ensure_quiz_launched(page, max(cfg.timeout_ms, 15000))
    if is_on_cover_page(page) and not page.locator('[data-testid="tunnel-vision-back-button"], button[aria-label="Back"]').first.is_visible(timeout=500):
        logger.error("Still on quiz cover page; aborting.")
        return
    if is_quiz_completed(page) or page.locator(':text("Reviewing your submission"), :text("hang tight")').first.is_visible():
        logger.info("Quiz already completed or under review. Polling next item CTA...")
        poll_and_click_next(page, max_wait_sec=cfg.post_quiz_wait_sec)
        return
    q_locs, questions = wait_and_extract_questions(page, cfg.timeout_ms)
    logger.info("Extracted %d quiz question(s).", len(questions))
    if not questions or not any(q.locator('input:not([disabled]), textarea:not([disabled])').count() or _is_textarea(q) for q in q_locs):
        logger.info("No active questions found. Polling next item CTA.")
        poll_and_click_next(page, max_wait_sec=cfg.post_quiz_wait_sec)
        return
    if not (answers := solve_quiz_with_llm(questions, cfg)):
        logger.error("No valid answers received from LLM; aborting quiz submission.")
        return
    for idx, q_loc in enumerate(q_locs):
        with suppress(Error):
            q_loc.scroll_into_view_if_needed(timeout=1000)
        ans, q_meta = answers.get(idx, []), (questions[idx] if idx < len(questions) else {})
        if not ans:
            continue
        if q_meta.get("type") == "textarea":
            with suppress(Error):
                _find_textarea(q_loc).fill(ans[0])
        else:
            for opt in ans:
                click_option(q_loc, opt, q_meta.get("options", []))
        page.wait_for_timeout(300)
    if (agree := page.locator('#agreement-checkbox-base, label:has-text("understand and agree")').first).is_visible(timeout=cfg.timeout_ms):
        with suppress(Error):
            agree.scroll_into_view_if_needed(timeout=1000)
            agree.click(force=True)
        page.wait_for_timeout(1000)
    submit_quiz(page, cfg)
