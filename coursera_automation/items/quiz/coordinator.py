"""Quiz interaction: extract questions, apply LLM answers, agree, and submit."""

import logging

from playwright.sync_api import Error, Page

from coursera_automation.config import Settings
from coursera_automation.items.navigation.dialogs import dismiss_dialogs
from coursera_automation.items.quiz.parser import wait_and_extract_questions
from coursera_automation.items.quiz.solver import solve_quiz_with_llm
from coursera_automation.items.quiz.status import is_quiz_completed

from .submit import NEXT_BTN, poll_and_click_next, submit_quiz

logger = logging.getLogger(__name__)
START_CTA = '[data-testid="CoverPageActionButton"], button:has-text("Start assignment"), button:has-text("Start"), button:has-text("Resume")'
REV_SEL = ':text("Reviewing your submission"), :text("hang tight")'


def handle_quiz(page: Page, cfg: Settings) -> None:
    """Handle complete quiz lifecycle: launch, solve, agree, and submit."""
    logger.info("Handling quiz assignment...")
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(2000)
    dismiss_dialogs(page)
    if (cta := page.locator(START_CTA).first).is_visible(timeout=3000):
        logger.info("Clicking quiz start/resume CTA...")
        try:
            cta.click(force=True, timeout=5000)
        except Error:
            pass
        dismiss_dialogs(page)
        page.wait_for_timeout(3000)
    elif page.locator(NEXT_BTN).first.is_visible(timeout=1000) or is_quiz_completed(page) or page.locator(REV_SEL).first.is_visible(timeout=1000):
        logger.info("Quiz already completed or under review. Polling next item CTA...")
        poll_and_click_next(page, max_wait_sec=300)
        return

    q_locs, questions = wait_and_extract_questions(page, cfg.timeout_ms)
    logger.info("Extracted %d quiz question(s).", len(questions))
    if not questions or not any(q.locator('input:not([disabled])').count() for q in q_locs):
        logger.info("No active/unsubmitted questions found. Polling next item CTA.")
        poll_and_click_next(page, max_wait_sec=300)
        return

    if not (answers := solve_quiz_with_llm(questions, cfg)):
        logger.error("No valid answers received from LLM; aborting quiz submission.")
        return

    for idx, q_loc in enumerate(q_locs):
        for opt in answers.get(idx, []):
            if (btn := q_loc.locator("label").filter(has_text=opt).first).is_visible():
                btn.click(force=True)
                page.wait_for_timeout(300)

    if (agree := page.locator('#agreement-checkbox-base, label:has-text(", understand and agree.")').first).is_visible(timeout=cfg.timeout_ms):
        agree.click(force=True)
        page.wait_for_timeout(1000)
    submit_quiz(page, cfg)
