"""Quiz interaction: extract questions, apply LLM answers, agree, and submit."""

import logging

from playwright.sync_api import Error, Page

from coursera_automation.config import Settings
from coursera_automation.items.dialogs import dismiss_dialogs
from coursera_automation.items.quiz_parser import wait_and_extract_questions
from coursera_automation.items.quiz_solver import solve_quiz_with_llm
from coursera_automation.items.quiz_status import is_quiz_completed
from coursera_automation.items.quiz_submit import submit_quiz

logger = logging.getLogger(__name__)


def handle_quiz(page: Page, cfg: Settings) -> None:
    """Handle complete quiz lifecycle: launch, solve, agree, and submit."""
    logger.info("Handling quiz assignment...")
    page.wait_for_load_state("domcontentloaded")
    dismiss_dialogs(page)
    if is_quiz_completed(page):
        logger.info("Quiz already completed or passed. Ready for next item.")
        return

    cta_sel = ('[data-testid="CoverPageActionButton"], button:has-text("Try again"), '
               'button:has-text("Start"), button:has-text("Resume"), button:has-text("assignment")')
    if (cta := page.locator(cta_sel).first).is_visible(timeout=4000):
        logger.info("Clicking quiz CTA (Start / Try again / Resume)...")
        try:
            cta.click(force=True, timeout=5000)
        except Error as exc:
            logger.warning("Quiz CTA click bypassed (%s); checking questions...", exc)
        logger.info("Clicked quiz CTA. Waiting for quiz questions to load...")
        page.wait_for_timeout(2000)
        dismiss_dialogs(page)
        page.wait_for_timeout(3000)

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
                btn.scroll_into_view_if_needed()
                btn.click(force=True)
                page.wait_for_timeout(300)

    agree_sel = '#agreement-checkbox-base, label:has-text(", understand and agree.")'
    if (agree := page.locator(agree_sel).first).is_visible(timeout=cfg.timeout_ms):
        agree.click(force=True)
        page.wait_for_timeout(1000)

    submit_quiz(page, cfg)
