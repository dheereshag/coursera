"""Quiz lifecycle: launch, solve, fill answers, agree, and submit."""

import logging
from contextlib import suppress

from playwright.sync_api import Error, Page

from coursera_automation.config import Settings
from coursera_automation.items.navigation.dialogs import dismiss_dialogs

from .parser import _find_textarea, _is_textarea, wait_and_extract_questions
from .solver import solve_quiz_with_llm
from .status import is_quiz_completed
from .submit import NEXT_BTN, poll_and_click_next, submit_quiz

logger = logging.getLogger(__name__)


def handle_quiz(page: Page, cfg: Settings) -> None:
    """Handle complete quiz lifecycle: launch, solve, agree, and submit."""
    logger.info("Handling quiz assignment...")
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(2000)
    dismiss_dialogs(page)
    start_cta = '[data-testid="CoverPageActionButton"], button:has-text("Start assignment"), button:has-text("Start"), button:has-text("Resume")'
    if (cta := page.locator(start_cta).first).is_visible(timeout=3000):
        with suppress(Error):
            cta.click(force=True, timeout=5000)
        page.wait_for_load_state("domcontentloaded")
        dismiss_dialogs(page)
        page.wait_for_timeout(4000)
    elif page.locator(NEXT_BTN).first.is_visible(timeout=1000) or is_quiz_completed(page) or page.locator(':text("Reviewing your submission"), :text("hang tight")').first.is_visible(timeout=1000):
        logger.info("Quiz already completed or under review. Polling next item CTA...")
        poll_and_click_next(page, max_wait_sec=300)
        return

    q_locs, questions = wait_and_extract_questions(page, cfg.timeout_ms)
    logger.info("Extracted %d quiz question(s).", len(questions))
    if not questions or not any(q.locator('input:not([disabled]), textarea:not([disabled])').count() or _is_textarea(q) for q in q_locs):
        logger.info("No active/unsubmitted questions found. Polling next item CTA.")
        poll_and_click_next(page, max_wait_sec=300)
        return
    if not (answers := solve_quiz_with_llm(questions, cfg)):
        logger.error("No valid answers received from LLM; aborting quiz submission.")
        return
    for idx, q_loc in enumerate(q_locs):
        with suppress(Error):
            q_loc.scroll_into_view_if_needed(timeout=1000)
        ans, ta = answers.get(idx, []), _find_textarea(q_loc)
        if ta.is_visible(timeout=200) and ans:
            ta.fill(ans[0])
        else:
            for opt in ans:
                if (btn := q_loc.locator("label").filter(has_text=opt).first).is_visible():
                    btn.locator('input[type="checkbox"]').first.check(force=True) if btn.locator('input[type="checkbox"]').count() else btn.click(force=True)
        page.wait_for_timeout(300)
    if (agree := page.locator('#agreement-checkbox-base, label:has-text(", understand and agree.")').first).is_visible(timeout=cfg.timeout_ms):
        agree.click(force=True)
        page.wait_for_timeout(1000)
    submit_quiz(page, cfg)
