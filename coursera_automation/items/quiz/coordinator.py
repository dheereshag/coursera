"""Quiz interaction: extract questions, apply LLM answers, agree, and submit."""

import logging

from playwright.sync_api import Error, Page

from coursera_automation.config import Settings
from coursera_automation.items.navigation.dialogs import dismiss_dialogs
from coursera_automation.items.quiz.parser import wait_and_extract_questions
from coursera_automation.items.quiz.solver import solve_quiz_with_llm
from coursera_automation.items.quiz.status import is_quiz_completed
from coursera_automation.items.quiz.submit import _wait_for_evaluation, submit_quiz

logger = logging.getLogger(__name__)


def handle_quiz(page: Page, cfg: Settings) -> None:
    """Handle complete quiz lifecycle: launch, solve, agree, and submit."""
    logger.info("Handling quiz assignment...")
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(2000)
    dismiss_dialogs(page)
    rev_sel = ':text("Reviewing your submission"), :text("hang tight")'
    if page.locator(rev_sel).first.is_visible(timeout=1000):
        logger.info("Quiz submission under review. Waiting for results...")
        _wait_for_evaluation(page, max_wait_sec=300)
        return
    if is_quiz_completed(page):
        logger.info("Quiz already completed or passed. Ready for next item.")
        return

    cta_sel = '[data-testid="CoverPageActionButton"], button:has-text("Try again"), button:has-text("Start"), button:has-text("Resume")'
    if (cta := page.locator(cta_sel).first).is_visible(timeout=4000):
        try:
            cta.click(force=True, timeout=5000)
        except Error as exc:
            logger.warning("Quiz CTA click bypassed (%s); checking questions...", exc)
        page.wait_for_timeout(5000)
        dismiss_dialogs(page)
        page.wait_for_timeout(5000)

    q_locs, questions = wait_and_extract_questions(page, cfg.timeout_ms)
    logger.info("Extracted %d quiz question(s).", len(questions))
    if not questions or not any(q.locator('input:not([disabled])').count() for q in q_locs):
        logger.info("No active/unsubmitted quiz questions found. Skipping.")
        return

    answers = solve_quiz_with_llm(questions, cfg)
    logger.info("Quiz answers received: %s", answers)
    for idx, q_loc in enumerate(q_locs):
        for opt in answers.get(idx, []):
            if (btn := q_loc.locator("label").filter(has_text=opt).first).is_visible():
                btn.click(force=True)
                page.wait_for_timeout(300)

    if (agree := page.locator('#agreement-checkbox-base, label:has-text(", understand and agree.")').first).is_visible(timeout=cfg.timeout_ms):
        agree.click(force=True)
        page.wait_for_timeout(1000)

    submit_quiz(page, cfg)
