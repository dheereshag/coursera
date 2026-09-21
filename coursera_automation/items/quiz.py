"""Quiz interaction: extract questions, apply LLM answers, agree, and submit."""

import json
import logging

from playwright.sync_api import Page

from coursera_automation.config import Settings
from coursera_automation.items.navigator import dismiss_dialogs
from coursera_automation.items.quiz_parser import (
    _detect_type,
    _extract_prompt,
    wait_and_extract_questions,
)
from coursera_automation.items.quiz_solver import solve_quiz_with_llm
from coursera_automation.items.quiz_submit import submit_quiz

logger = logging.getLogger(__name__)

__all__ = ["_detect_type", "_extract_prompt", "handle_quiz"]


def handle_quiz(page: Page, cfg: Settings) -> None:
    """Handle complete quiz lifecycle: launch, solve, agree, and submit."""
    logger.info("Handling quiz assignment...")
    dismiss_dialogs(page)
    cta = page.locator(
        '[data-testid="CoverPageActionButton"], button:has-text("Start"), '
        'button:has-text("Resume"), button:has-text("Try again"), button:has-text("assignment")'
    ).first
    if cta.is_visible(timeout=5000):
        logger.info("Clicking quiz CTA...")
        cta.click()
        page.wait_for_timeout(2000)
        dismiss_dialogs(page)

    q_locs, questions = wait_and_extract_questions(page, cfg.timeout_ms)
    logger.info("Extracted %d quiz question(s):\n%s", len(questions), json.dumps(questions, indent=2, default=str))
    if not questions:
        logger.warning("No quiz questions found after waiting. Skipping submission.")
        return

    answers = solve_quiz_with_llm(questions, cfg)
    logger.info("Quiz answers received: %s", answers)
    for idx, q_loc in enumerate(q_locs):
        for opt in answers.get(idx, []):
            if (btn := q_loc.locator("label").filter(has_text=opt).first).is_visible():
                btn.scroll_into_view_if_needed()
                btn.click()

    if (agree := page.locator('#agreement-checkbox-base, label:has-text(", understand and agree.")').first).is_visible(
        timeout=cfg.timeout_ms
    ):
        agree.click(force=True)

    submit_quiz(page, cfg)
